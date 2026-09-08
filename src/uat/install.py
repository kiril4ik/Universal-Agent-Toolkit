"""The install engine.

Contract:
  * Everything the toolkit adds lives under <project>/.agent-toolkit/ -
    one folder, easy to inspect, easy to delete.
  * Outside that folder we create ONLY the files the selected agents
    actually need. Selecting Claude Code never creates .cursor/.
  * Skills are stored once and mounted into tool-native locations by
    symlink, so no content is duplicated on disk.
  * Existing files are never overwritten without --force.
"""

from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass, field
from pathlib import Path

from . import render
from .catalog import Catalog, Pack
from .detect import Detection, detect, looks_like_new_project
from .mcpconf import ServerSpec, manual_setup_notes, write_agent_mcp
from .registry import Agent, Registry
from .util import (
    ADD,
    OVERWRITE,
    SAME,
    CONFLICT,
    Report,
    ToolkitError,
    copy_file,
    copy_tree,
    dumps_json,
    iter_files,
    link_or_copy,
    read_json,
    sha256_file,
    supports_symlinks,
    write_text,
)

TOOLKIT_DIR = ".agent-toolkit"
STATE_FILE = "installed.json"
PROJECT_FILE = "project.json"
MODES = ("thorough", "focused", "autonomous")


@dataclass
class InstallPlan:
    project: Path
    agents: list[Agent]
    packs: list[Pack]
    mode: str
    detection: Detection
    skills_mode: str = "link"       # "link" | "copy"
    new_project: bool = False

    @property
    def pack_ids(self) -> list[str]:
        return [p.id for p in self.packs]

    @property
    def agent_ids(self) -> list[str]:
        return [a.id for a in self.agents]

    def files_outside_toolkit(self) -> list[str]:
        out: list[str] = []
        for a in self.agents:
            out.extend(a.owned_paths())
        return sorted(set(out))


@dataclass
class InstallResult:
    report: Report
    plan: InstallPlan
    mcp_specs: list[ServerSpec] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.report.conflicts()


# ----------------------------------------------------------------------
# planning
# ----------------------------------------------------------------------

def build_plan(
    toolkit_root: Path,
    project: Path,
    *,
    registry: Registry,
    catalog: Catalog,
    agent_keys: list[str],
    mode: str,
    profile: str | None = None,
    explicit_packs: list[str] | None = None,
    add_packs: list[str] | None = None,
    all_packs: bool = False,
    skills_mode: str | None = None,
) -> InstallPlan:
    if mode not in MODES:
        raise ToolkitError(f"mode must be one of {', '.join(MODES)}, got {mode!r}")
    if not agent_keys:
        raise ToolkitError(
            "no agent selected. Pass --agent (e.g. --agent claude-code) or --agent all"
        )

    if len(agent_keys) == 1 and agent_keys[0] == "all":
        agents = list(registry)
    else:
        agents = registry.resolve(agent_keys)

    detection = detect(project)

    if all_packs:
        selected = set(catalog.ids)
    elif explicit_packs:
        selected = catalog.expand(set(explicit_packs))
    elif profile:
        selected = catalog.resolve_profile(profile)
    else:
        selected = catalog.recommend(detection.tokens)

    if add_packs:
        selected = catalog.expand(selected | set(add_packs))

    for pid in selected:
        catalog.get(pid)  # validates

    if skills_mode is None:
        skills_mode = "link" if supports_symlinks(project / TOOLKIT_DIR) else "copy"

    return InstallPlan(
        project=project,
        agents=agents,
        packs=[catalog.get(p) for p in sorted(selected)],
        mode=mode,
        detection=detection,
        skills_mode=skills_mode,
        new_project=looks_like_new_project(project),
    )


# ----------------------------------------------------------------------
# execution
# ----------------------------------------------------------------------

def _install_pack_files(
    pack: Pack, toolkit_root: Path, dest_root: Path, *, force: bool, report: Report
) -> None:
    """Copy a pack's own files, then any vendored snapshots it maps in."""
    copy_tree(pack.files_dir, dest_root, force=force, report=report)

    for vm in pack.vendor_maps:
        vendor_root = toolkit_root / "vendor" / vm.vendor
        if not vendor_root.exists():
            report.record(
                CONFLICT,
                vendor_root,
                f"pack '{pack.id}' needs vendor '{vm.vendor}'; run `uat vendor sync`",
            )
            continue
        # explicit file mapping: vendored names become clean rule names
        if vm.files:
            for rel_from, rel_to in vm.files:
                f_src = vendor_root / rel_from
                if not f_src.is_file():
                    report.record(
                        CONFLICT, f_src, f"vendor file missing for pack '{pack.id}'"
                    )
                    continue
                copy_file(f_src, dest_root / rel_to, force=force, report=report)
            if not vm.src:
                continue

        src = vendor_root / vm.src if vm.src else vendor_root
        if not src.exists():
            report.record(CONFLICT, src, f"vendor path missing for pack '{pack.id}'")
            continue

        dest = dest_root / vm.dest
        if vm.only:
            for child in vm.only:
                child_src = src / child
                if not child_src.exists():
                    report.record(CONFLICT, child_src, f"vendor subpath missing ({pack.id})")
                    continue
                if child_src.is_dir():
                    copy_tree(child_src, dest / child, force=force, report=report)
                else:
                    copy_file(child_src, dest / child, force=force, report=report)
        else:
            for f in iter_files(src):
                rel = f.relative_to(src)
                if any(str(rel).startswith(e) for e in vm.exclude):
                    continue
                copy_file(f, dest / rel, force=force, report=report)


def write_agent_hooks(
    agent: Agent, project: Path, *, enabled: bool, force: bool, report: Report
) -> bool:
    """Register our SessionStart hook in the agent's settings, merging safely.

    Settings files usually contain the user's own configuration, so this only
    adds our entry and leaves everything else untouched.
    """
    import json

    cfg = agent.surfaces.get("hooks") or {}
    if not enabled or cfg.get("scope") != "project" or not cfg.get("path"):
        return False

    script = f"$CLAUDE_PROJECT_DIR/{TOOLKIT_DIR}/hooks/session-start.sh"
    if not (project / TOOLKIT_DIR / "hooks" / "session-start.sh").is_file():
        return False

    path = project / cfg["path"]
    if path.exists():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report.record(CONFLICT, path, "not valid JSON; hook not registered")
            return False
        if not isinstance(doc, dict):
            report.record(CONFLICT, path, "not a JSON object; hook not registered")
            return False
    else:
        doc = {}

    key, event = cfg.get("key", "hooks"), cfg.get("event", "SessionStart")
    hooks = doc.setdefault(key, {})
    if not isinstance(hooks, dict):
        report.record(CONFLICT, path, f"existing '{key}' is not an object; kept")
        return False
    entries = hooks.setdefault(event, [])
    if not isinstance(entries, list):
        report.record(CONFLICT, path, f"existing '{event}' is not a list; kept")
        return False

    ours = {
        "matcher": cfg.get("matcher", "startup|clear|compact"),
        "hooks": [{"type": "command", "command": script}],
    }
    for existing in entries:
        if json.dumps(existing, sort_keys=True) == json.dumps(ours, sort_keys=True):
            report.record(SAME, path, "SessionStart hook")
            return True
        if TOOLKIT_DIR in json.dumps(existing):
            if not force:
                report.record(CONFLICT, path, "a different toolkit hook exists; kept")
                return False
            entries.remove(existing)
            break

    entries.append(ours)
    if not report.dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dumps_json(doc), encoding="utf-8")
    report.record(ADD, path, "SessionStart hook")
    return True


def _collect_mcp_specs(dest_root: Path) -> list[ServerSpec]:
    mcp_dir = dest_root / "mcp"
    if not mcp_dir.exists():
        return []
    return [ServerSpec.from_json(p) for p in sorted(mcp_dir.glob("*.json"))]


def _installed_rules(dest_root: Path) -> list[str]:
    d = dest_root / "rules"
    return sorted(p.name for p in d.glob("*.md")) if d.exists() else []


def _installed_skills(dest_root: Path) -> list[str]:
    d = dest_root / "skills"
    if not d.exists():
        return []
    return sorted(p.name for p in d.iterdir() if p.is_dir() and (p / "SKILL.md").exists())


def execute(
    plan: InstallPlan,
    toolkit_root: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> InstallResult:
    report = Report(dry_run=dry_run)
    project = plan.project
    dest = project / TOOLKIT_DIR
    result = InstallResult(report=report, plan=plan)

    if not project.exists():
        if dry_run:
            raise ToolkitError(f"project directory does not exist: {project}")
        project.mkdir(parents=True, exist_ok=True)

    # 1. our own always-on policy + the planning workflow
    copy_tree(toolkit_root / "catalog" / "core", dest / "core", force=force, report=report)
    copy_tree(
        toolkit_root / "catalog" / "workflow", dest / "workflow", force=force, report=report
    )

    # 2. packs
    for pack in plan.packs:
        _install_pack_files(pack, toolkit_root, dest, force=force, report=report)

    # 3. reports directory
    write_text(
        dest / "reports" / "README.md",
        "# Phase reports\n\n"
        "Each completed workflow phase writes one file here, named `NN-phase.md`.\n"
        "They are the project's decision log - read them before re-planning.\n",
        force=force,
        report=report,
    )

    uat_cmd = render.uat_invocation(project, toolkit_root)
    hook_script = dest / "hooks" / "session-start.sh"
    if hook_script.is_file() and not dry_run:
        hook_script.chmod(0o755)

    rules = _installed_rules(dest)
    skills = _installed_skills(dest)
    specs = _collect_mcp_specs(dest)
    result.mcp_specs = specs

    has_workflow = (dest / "workflow" / "README.md").exists() or not dry_run
    has_deploy = (dest / "deploy").exists() or (dest / "docker").exists()

    # 4. agent adapters - ONLY for the selected agents
    wrote_agents_md = False
    for agent in plan.agents:
        mount = None
        if agent.supports_skills and skills:
            mount = agent.skills_path

        ctx = render.RenderContext(
            project_name=project.resolve().name,
            mode=plan.mode,
            agents=plan.agent_ids,
            rules=rules,
            skills=skills,
            mcp_servers=[s.name for s in specs],
            has_workflow=has_workflow,
            has_deploy=has_deploy,
            skills_mount=mount,
            uat_cmd=uat_cmd,
        )

        # instruction file
        ipath = agent.instruction_path
        if ipath:
            target = project / ipath
            body = render.instructions_for(agent, ctx)
            if target.exists() and not force:
                existing = target.read_text(encoding="utf-8", errors="replace")
                if render.TOOLKIT_DIR not in existing:
                    report.record(
                        CONFLICT,
                        target,
                        "existing instructions do not reference the toolkit; kept",
                    )
                else:
                    write_text(target, body, force=force, report=report)
            else:
                write_text(target, body, force=force, report=report)

        # shared AGENTS.md
        for extra in agent.extra_root_files:
            if extra == "AGENTS.md" and wrote_agents_md:
                continue
            write_text(project / extra, render.agents_md(ctx), force=force, report=report)
            if extra == "AGENTS.md":
                wrote_agents_md = True

        # skills mount
        if mount:
            link_or_copy(
                dest / "skills",
                project / mount,
                mode=plan.skills_mode,
                force=force,
                report=report,
            )

        # slash commands - the workflow needs a trigger, not just a mention
        cmd_surface = agent.surfaces.get("commands")
        if cmd_surface and cmd_surface.get("path") and has_workflow:
            cmd_dir = project / cmd_surface["path"]
            for filename, body in render.claude_commands(ctx).items():
                write_text(cmd_dir / filename, body, force=force, report=report)

        # session-start hook - makes the rules unmissable rather than findable
        if write_agent_hooks(
            agent, project,
            enabled=(dest / "hooks" / "session-start.sh").is_file(),
            force=force, report=report,
        ):
            result.notes.append(
                f"{agent.name}: a SessionStart hook was registered in "
                f"{agent.surfaces['hooks']['path']}. Your tool will ask you to "
                "approve it the first time - that prompt is expected."
            )

        # mcp
        write_agent_mcp(agent, project, specs, force=force, report=report)

    # 5. CORE.md router (after adapters so it reflects the real mounts)
    primary_mount = next(
        (a.skills_path for a in plan.agents if a.supports_skills and skills), None
    )
    core_ctx = render.RenderContext(
        project_name=project.resolve().name,
        mode=plan.mode,
        agents=plan.agent_ids,
        rules=rules,
        skills=skills,
        mcp_servers=[s.name for s in specs],
        has_workflow=has_workflow,
        has_deploy=has_deploy,
        skills_mount=primary_mount,
        uat_cmd=uat_cmd,
    )
    core_path = dest / "CORE.md"
    core_body = render.core_md(core_ctx)
    if core_path.exists():
        existing = core_path.read_text(encoding="utf-8", errors="replace")
        core_body = render.preserve_user_tail(existing, core_body)
    write_text(core_path, core_body, force=True, report=report)

    # 5b. the human-facing entry point
    if has_workflow:
        wants_commands = any(
            a.surfaces.get("commands", {}).get("path") for a in plan.agents
        )
        write_text(
            dest / "START-HERE.md",
            render.start_here(core_ctx, claude=wants_commands),
            force=True,
            report=report,
        )

    # 6. MCP readme
    if specs:
        write_text(
            dest / "mcp" / "README.md",
            manual_setup_notes(plan.agents, specs),
            force=True,
            report=report,
        )
        for spec in specs:
            if spec.needs_manual_setup:
                result.notes.append(
                    f"MCP '{spec.name}' needs manual setup: "
                    + ", ".join(spec.required_env + spec.required_apps)
                )
        for agent in plan.agents:
            if agent.mcp_scope == "global":
                result.notes.append(
                    f"{agent.name} stores MCP config globally "
                    f"({agent.mcp.get('path')}) - add servers manually."
                )

    # 7. state
    _write_state(dest, plan, toolkit_root, force=True, report=report)

    return result


def _write_state(
    dest: Path, plan: InstallPlan, toolkit_root: Path, *, force: bool, report: Report
) -> None:
    now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()

    project_doc = {
        "mode": plan.mode,
        "agents": plan.agent_ids,
        "detected_stack": sorted(plan.detection.tokens),
        "detection_evidence": {
            k: v for k, v in sorted(plan.detection.evidence.items())
        },
        "new_project": plan.new_project,
        "updated_at": now,
    }
    existing = read_json(dest / PROJECT_FILE, default={})
    if existing:
        # preserve human-authored keys we do not manage
        for key in existing:
            if key not in project_doc:
                project_doc[key] = existing[key]
    write_text(dest / PROJECT_FILE, dumps_json(project_doc), force=True, report=report)

    # Record the hash of what the toolkit actually installed - NOT whatever is
    # on disk afterwards. A file we refused to overwrite must keep its previous
    # recorded hash, otherwise the user's edit silently becomes the baseline
    # and `uat status` would report no drift.
    previous: dict[str, str] = read_json(dest / STATE_FILE, default={}).get("files", {})
    files: dict[str, str] = dict(previous)

    if not report.dry_run:
        for action in report.actions:
            try:
                rel = str(Path(action.path).relative_to(dest)).replace(os.sep, "/")
            except ValueError:
                continue                      # outside .agent-toolkit/
            if rel in (STATE_FILE, PROJECT_FILE):
                continue
            if action.kind in (ADD, OVERWRITE, SAME):
                p = dest / rel
                if p.is_file():
                    files[rel] = sha256_file(p)
            # CONFLICT: deliberately keep the previous hash so drift is visible.

    state = {
        "toolkit_version": _toolkit_version(toolkit_root),
        "installed_at": now,
        "skills_mode": plan.skills_mode,
        "packs": plan.pack_ids,
        "agents": plan.agent_ids,
        "files": files,
    }
    write_text(dest / STATE_FILE, dumps_json(state), force=True, report=report)


def _toolkit_version(toolkit_root: Path) -> str:
    vf = toolkit_root / "VERSION"
    if vf.exists():
        return vf.read_text(encoding="utf-8").strip()
    return "0.0.0-dev"


# ----------------------------------------------------------------------
# status / uninstall
# ----------------------------------------------------------------------

def load_state(project: Path) -> dict:
    return read_json(project / TOOLKIT_DIR / STATE_FILE, default={})


def drift(project: Path) -> tuple[list[str], list[str]]:
    """Return (modified, missing) files relative to the recorded install."""
    state = load_state(project)
    recorded: dict[str, str] = state.get("files", {})
    dest = project / TOOLKIT_DIR
    modified, missing = [], []
    for rel, digest in sorted(recorded.items()):
        p = dest / rel
        if not p.exists():
            missing.append(rel)
        elif sha256_file(p) != digest:
            modified.append(rel)
    return modified, missing


def uninstall(
    project: Path, registry: Registry, *, report: Report, keep_toolkit: bool = False
) -> None:
    """Remove generated agent surfaces. Never touches unrelated project files."""
    import shutil

    state = load_state(project)
    if not state:
        raise ToolkitError(
            f"no toolkit installation found in {project} "
            f"(missing {TOOLKIT_DIR}/{STATE_FILE})"
        )

    dest = project / TOOLKIT_DIR

    # Server names we added, read before the toolkit directory goes away.
    our_servers = {s.name for s in _collect_mcp_specs(dest)}

    touched_dirs: set[Path] = set()

    for agent_id in state.get("agents", []):
        try:
            agent = registry.get(agent_id)
        except ToolkitError:
            continue

        mcp_path = agent.mcp.get("path") if agent.writes_project_mcp else None

        for rel in agent.owned_paths():
            target = project / rel
            touched_dirs.add(target.parent)

            # Settings files hold the user's own config: remove only our hook.
            hooks_cfg = agent.surfaces.get("hooks") or {}
            if hooks_cfg.get("path") and rel == hooks_cfg["path"]:
                _strip_our_hook(target, hooks_cfg, report=report)
                continue

            # MCP configs are shared with servers we know nothing about:
            # surgically remove only our entries.
            if mcp_path and rel == mcp_path:
                _strip_our_mcp_servers(target, agent, our_servers, report=report)
                continue

            if target.is_symlink():
                if not report.dry_run:
                    target.unlink()
                report.record("skip", target, "removed symlink")
            elif target.is_file():
                text = target.read_text(encoding="utf-8", errors="replace")
                if TOOLKIT_DIR in text:
                    if not report.dry_run:
                        target.unlink()
                    report.record("skip", target, "removed generated file")
                else:
                    report.record(CONFLICT, target, "not generated by uat; kept")
            elif target.is_dir():
                # A directory surface (.claude/commands, .cursor/rules ...):
                # remove the files we generated, leave anything else alone.
                for f in sorted(p for p in target.rglob("*") if p.is_file()):
                    try:
                        text = f.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    if TOOLKIT_DIR in text:
                        if not report.dry_run:
                            f.unlink()
                        report.record("skip", f, "removed generated file")
                    else:
                        report.record(CONFLICT, f, "not generated by uat; kept")
                    touched_dirs.add(f.parent)
                touched_dirs.add(target)

    if not keep_toolkit and dest.exists():
        if not report.dry_run:
            shutil.rmtree(dest)
        report.record("skip", dest, "removed toolkit directory")

    # Prune directories we emptied, climbing to the project root but never
    # removing it - so .windsurf/rules/ going away also takes .windsurf/.
    for start in sorted(touched_dirs, key=lambda p: len(p.parts), reverse=True):
        d = start
        while d != project and project in d.parents:
            try:
                if not d.is_dir() or any(d.iterdir()):
                    break
                if not report.dry_run:
                    d.rmdir()
                report.record("skip", d, "removed empty directory")
            except OSError:
                break
            d = d.parent


def _strip_our_hook(path: Path, cfg: dict, *, report: Report) -> None:
    """Remove our SessionStart hook, keeping any other settings intact."""
    import json

    if not path.is_file():
        return
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        report.record(CONFLICT, path, "not valid JSON; left untouched")
        return
    if not isinstance(doc, dict):
        return

    key, event = cfg.get("key", "hooks"), cfg.get("event", "SessionStart")
    entries = (doc.get(key) or {}).get(event)
    if not isinstance(entries, list):
        return

    kept = [e for e in entries if TOOLKIT_DIR not in json.dumps(e)]
    if len(kept) == len(entries):
        return

    if kept:
        doc[key][event] = kept
    else:
        doc[key].pop(event, None)
        if not doc[key]:
            doc.pop(key, None)

    if not doc:
        if not report.dry_run:
            path.unlink()
        report.record("skip", path, "removed (only held our hook)")
        return

    if not report.dry_run:
        path.write_text(dumps_json(doc), encoding="utf-8")
    report.record("skip", path, "removed our hook, kept other settings")


def _strip_our_mcp_servers(
    path: Path, agent: Agent, names: set[str], *, report: Report
) -> None:
    """Remove only the servers this toolkit added, leaving the rest intact."""
    import json

    if not path.is_file():
        return
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        report.record(CONFLICT, path, "not valid JSON; left untouched")
        return
    if not isinstance(doc, dict):
        report.record(CONFLICT, path, "not a JSON object; left untouched")
        return

    key = agent.mcp.get("key") or "mcpServers"
    bucket = doc.get(key)
    if not isinstance(bucket, dict):
        return

    removed = [n for n in names if n in bucket]
    for n in removed:
        del bucket[n]

    if not removed:
        return

    # If nothing of ours or anyone else's remains, drop the file entirely.
    leftover = {k: v for k, v in doc.items() if not (k == key and not bucket)}
    if not leftover:
        if not report.dry_run:
            path.unlink()
        report.record("skip", path, f"removed (only held our {len(removed)} server(s))")
        return

    if not report.dry_run:
        path.write_text(dumps_json(leftover), encoding="utf-8")
    report.record("skip", path, f"removed {len(removed)} server(s), kept the rest")


def refresh(project: Path, toolkit_root: Path, registry: Registry, *, report: Report) -> None:
    """Re-render CORE.md and START-HERE.md from what is on disk.

    Anything that changes the installed rule set - `uat add-rule`, or a human
    dropping a file into rules/ - would otherwise leave the router listing a
    stale set. The router is generated, so regenerating it is the fix.
    """
    dest = project / TOOLKIT_DIR
    state = read_json(dest / STATE_FILE, default={})
    doc = read_json(dest / PROJECT_FILE, default={})
    if not state:
        raise ToolkitError(f"no toolkit installation in {project}")

    agents = []
    for aid in state.get("agents", []):
        try:
            agents.append(registry.get(aid))
        except ToolkitError:
            continue

    specs = _collect_mcp_specs(dest)
    skills = _installed_skills(dest)
    primary_mount = next(
        (a.skills_path for a in agents if a.supports_skills and skills), None
    )
    ctx = render.RenderContext(
        project_name=project.resolve().name,
        mode=doc.get("mode", "focused"),
        agents=[a.id for a in agents],
        rules=_installed_rules(dest),
        skills=skills,
        mcp_servers=[s.name for s in specs],
        has_workflow=(dest / "workflow" / "README.md").is_file(),
        has_deploy=(dest / "deploy").exists() or (dest / "docker").exists(),
        skills_mount=primary_mount,
        uat_cmd=render.uat_invocation(project, toolkit_root),
    )

    core_path = dest / "CORE.md"
    body = render.core_md(ctx)
    if core_path.exists():
        body = render.preserve_user_tail(core_path.read_text(encoding="utf-8"), body)
    write_text(core_path, body, force=True, report=report)

    if ctx.has_workflow:
        write_text(
            dest / "START-HERE.md",
            render.start_here(
                ctx, claude=any(a.surfaces.get("commands", {}).get("path") for a in agents)
            ),
            force=True, report=report,
        )
