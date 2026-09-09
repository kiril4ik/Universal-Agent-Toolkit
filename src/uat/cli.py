"""Command line interface."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from . import embed as embedlib
from . import install as inst
from . import vendorlib
from .catalog import Catalog, TIERS
from .detect import detect
from .registry import Registry
from .util import Report, ToolkitError, bold, cyan, dim, green, red, yellow

TOOLKIT_ROOT = Path(__file__).resolve().parents[2]


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------

def _load(root: Path) -> tuple[Registry, Catalog]:
    return Registry.load(root), Catalog.load(root)


def _project(args) -> Path:
    return Path(args.project).expanduser().resolve()


def _interactive_packs(catalog: Catalog, recommended: set[str], detection) -> set[str]:
    from .picker import choose_packs

    return choose_packs(catalog, recommended, detection)


def _choose_mode() -> str:
    print()
    print(bold("How autonomous should the agent be?"))
    print("  1  thorough    ask every question that materially affects the result")
    print("  2  focused     ask only blocking questions, use sensible defaults  " + dim("(default)"))
    print("  3  autonomous  decide independently; interrupt only for risky or ambiguous calls")
    print()
    try:
        answer = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise ToolkitError("cancelled")
    return {"1": "thorough", "2": "focused", "3": "autonomous", "": "focused"}.get(
        answer, "focused"
    )


# ----------------------------------------------------------------------
# commands
# ----------------------------------------------------------------------

def cmd_agents(args) -> int:
    registry, _ = _load(TOOLKIT_ROOT)
    if args.show:
        agent = registry.get(args.show)
        print(bold(f"{agent.name}  ({agent.id})"))
        print(f"  confidence     {agent.confidence}")
        print(f"  instructions   {agent.instruction_path or '-'}")
        print(f"  extra files    {', '.join(agent.extra_root_files) or '-'}")
        print(f"  skills         {agent.skills_path or dim('not supported')}")
        print(f"  mcp            {agent.mcp.get('path') or '-'}  ({agent.mcp_scope})")
        if agent.notes:
            print(f"\n  {dim(agent.notes)}")
        print(f"\n  {bold('creates in your project:')}")
        for p in agent.owned_paths():
            print(f"    {p}")
        return 0

    print(bold(f"{len(registry)} supported agents"))
    print()
    for a in registry:
        conf = {"high": green, "medium": yellow, "low": red}[a.confidence]("*")
        skills = green("skills") if a.supports_skills else dim("no skills")
        mcp = {
            "project": green("mcp"),
            "global": yellow("mcp:global"),
            "unsupported": dim("no mcp"),
        }[a.mcp_scope]
        print(f"  {conf} {a.id:<14} {a.instruction_path or '':<32} {skills:<16} {mcp}")
    print()
    print(dim("  * confidence in the format spec: green=high, yellow=medium, red=low"))
    print(dim("    formats live in catalog/agents.json - correct them there, not in code"))
    return 0


def cmd_catalog(args) -> int:
    _, catalog = _load(TOOLKIT_ROOT)
    if getattr(args, "search", None):
        from .catalog import search_rule_documents
        hits = search_rule_documents(TOOLKIT_ROOT, args.search)
        if not hits:
            print(dim(f"  nothing matches {args.search!r}"))
            return 0
        print(bold(f"{len(hits)} vendored rule document(s) matching {args.search!r}"))
        packed = {f["from"].split("/")[-1] for p in catalog
                  for vm in p.vendor_maps for f in
                  [{"from": s} for s, _ in vm.files]}
        for vendor, stem, size in hits:
            note = ""
            for p in catalog:
                for vm in p.vendor_maps:
                    for frm, _ in vm.files:
                        if vm.vendor == vendor and frm.split("/")[-1].startswith(stem + "."):
                            note = green(f"  (pack: {p.id})")
            print(f"  {vendor:<22} {stem:<48} {dim(str(size) + ' B')}{note}")
        print()
        print(dim("  install one with:  uat add-rule <vendor>:<name> --project ."))
        return 0

    if getattr(args, "unmapped", False):
        from .catalog import unmapped_rule_files, unreachable_vendor_content
        print(bold("Vendored content with no pack"))
        orphans = unreachable_vendor_content(catalog, TOOLKIT_ROOT)
        if orphans:
            print(f"\n  {red('unreachable skills')} - vendored but not installable:")
            for vendor, names in orphans.items():
                for n in names:
                    print(f"    {vendor}/{n}")
        for vendor, count in sorted(unmapped_rule_files(catalog, TOOLKIT_ROOT).items()):
            print(f"\n  {vendor}: {yellow(str(count))} rule file(s) with no pack")
            sub = {"awesome-copilot": ("instructions", ".instructions.md"),
                   "awesome-cursorrules": ("rules", ".mdc")}[vendor]
            base = TOOLKIT_ROOT / "vendor" / vendor / sub[0]
            used = {f["from"].split("/")[-1]
                    for p in catalog for vm in p.vendor_maps for f in
                    [{"from": s} for s, _ in vm.files] if vm.vendor == vendor}
            names = sorted(f.name.replace(sub[1], "") for f in base.glob("*" + sub[1])
                           if f.name not in used)
            for i in range(0, min(len(names), 60), 6):
                print("    " + "  ".join(f"{n:<22}" for n in names[i:i + 6]))
            if len(names) > 60:
                print(dim(f"    ... and {len(names) - 60} more"))
        print()
        print(dim("  Add one with a pack.json - see docs/ARCHITECTURE.md"))
        return 0
    print(bold(f"{len(catalog)} packs"))
    last = None
    for pack in catalog:
        if pack.tier != last:
            print(f"\n  {bold(pack.tier.upper())}")
            last = pack.tier
        prov = pack.provides()
        bits = [f"{v} {k}" for k, v in prov.items() if v]
        vend = cyan(" vendored") if pack.vendor_maps else ""
        print(f"    {pack.id:<26} {pack.title:<34} {dim(', '.join(bits))}{vend}")
    if catalog.profiles:
        print(f"\n  {bold('PROFILES')}")
        for name in sorted(catalog.profiles):
            ids = catalog.resolve_profile(name)
            print(f"    {name:<26} {dim(f'{len(ids)} packs')}")
    return 0


def cmd_detect(args) -> int:
    project = _project(args)
    d = detect(project)
    print(bold(f"Stack detection: {project}"))
    if not d.tokens:
        print(dim("  nothing detected - looks like a new/empty project"))
        return 0
    for token in sorted(d.tokens):
        print(f"  {green(token):<28} {dim(d.why(token))}")
    return 0


def _resolve_selection(args, registry, catalog, project):
    detection = detect(project)
    if args.all:
        recommended = set(catalog.ids)
    elif args.packs:
        recommended = catalog.expand(set(args.packs))
    elif args.profile:
        recommended = catalog.resolve_profile(args.profile)
    else:
        recommended = catalog.recommend(detection.tokens)
    return detection, recommended


def _path_symlink_target() -> Path | None:
    """A directory already on PATH, inside $HOME, that we can write to.

    Only somewhere already on PATH: creating a directory the shell does not
    search would report success and change nothing. If there is no such
    place, the caller prints the command instead of guessing at a shell
    config file it does not own.
    """
    home = Path.home()
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        d = Path(entry)
        try:
            if d.is_dir() and home in d.parents and os.access(d, os.W_OK):
                return d
        except OSError:
            continue
    return None


def _offer_path_symlink(toolkit_root: Path) -> None:
    """Ask before putting `uat` on PATH. Never runs non-interactively.

    The generated CORE.md tells the agent to run bare `uat`, so on a
    non-embedded install this is a prerequisite, not a convenience.
    """
    launcher = toolkit_root / "bin" / "uat"
    if not launcher.is_file():
        return

    target = _path_symlink_target()
    print()
    print(bold("`uat` is not on your PATH."))
    print(dim("  The generated .agent-toolkit/CORE.md tells your agent to run it -"))
    print(dim("  phase 05 installs the stack's rule packs that way."))
    if target is None:
        print(f"  Add it yourself:  ln -s {launcher} <a directory on your PATH>")
        return

    link = target / "uat"
    print()
    try:
        answer = input(f"Symlink it into {target}? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if answer in ("n", "no"):
        print(dim(f"  skipped - ln -s {launcher} {link}"))
        return

    if link.exists() or link.is_symlink():
        print(red(f"  {link} already exists - left alone"))
        print(dim(f"  replace it yourself with: ln -sfn {launcher} {link}"))
        return
    try:
        link.symlink_to(launcher)
    except OSError as exc:
        print(red(f"  could not create {link}: {exc}"))
        return
    print(green(f"  {link} -> {launcher}"))
    print(dim("  remove it with: rm " + str(link)))


def cmd_install(args) -> int:
    registry, catalog = _load(TOOLKIT_ROOT)
    project = _project(args)

    interactive = (sys.stdin.isatty() and sys.stdout.isatty()
                   and not args.yes and not args.dry_run)

    # An install into a configured project EXTENDS it. Anything else means
    # `--add go` silently drops the packs, agents and mode already recorded -
    # which is exactly the documented mid-project flow in workflow phase 05.
    previous = inst.load_state(project)
    prev_doc = inst.read_json(
        project / inst.TOOLKIT_DIR / inst.PROJECT_FILE, default={})
    merging = bool(previous) and not args.replace

    mode = args.mode
    if mode is None and merging and prev_doc.get("mode") in inst.MODES:
        mode = prev_doc["mode"]
    if mode is None:
        mode = _choose_mode() if interactive else "focused"

    detection, recommended = _resolve_selection(args, registry, catalog, project)

    if merging:
        explicit = bool(args.packs or args.profile or args.all)
        known = set(catalog.ids)
        prev_packs = {p for p in previous.get("packs", []) if p in known}
        if not explicit:
            recommended = prev_packs | recommended
        else:
            recommended |= prev_packs
        prev_agents = [a for a in previous.get("agents", []) if a in registry.ids]
        for aid in prev_agents:
            if aid not in args.agent:
                args.agent.append(aid)

    if interactive and not args.packs and not args.all and not args.profile:
        recommended = _interactive_packs(catalog, recommended, detection)

    plan = inst.build_plan(
        TOOLKIT_ROOT,
        project,
        registry=registry,
        catalog=catalog,
        agent_keys=args.agent,
        mode=mode,
        explicit_packs=sorted(recommended),
        add_packs=args.add,
        skills_mode="copy" if args.copy else None,
    )

    print()
    print(bold("Install plan"))
    print(f"  project   {project}")
    print(f"  agents    {', '.join(a.name for a in plan.agents)}")
    print(f"  mode      {plan.mode}")
    print(f"  packs     {len(plan.packs)}  " + dim(", ".join(plan.pack_ids)))
    if merging:
        print(dim(f"            (extending the existing install; "
                  f"--replace to start over)"))
    print(f"  skills    {plan.skills_mode}")
    print()
    print(f"  {bold('creates one folder:')} .agent-toolkit/")
    outside = plan.files_outside_toolkit()
    print(f"  {bold('plus only these tool files:')}")
    for p in outside:
        print(f"    {p}")
    print()

    if args.dry_run:
        result = inst.execute(plan, TOOLKIT_ROOT, force=args.force, dry_run=True)
        print(bold("Dry run - no changes written"))
        rendered = result.report.render(project, verbose=args.verbose)
        if rendered:
            print(rendered)
        print(f"\n  {result.report.summary()}")
        return 0

    if interactive:
        try:
            if input("Proceed? [Y/n] ").strip().lower() in ("n", "no"):
                print("aborted")
                return 1
        except (EOFError, KeyboardInterrupt):
            print()
            return 1

    # Embed first: the generated files reference the CLI, and an embedded
    # launcher is the portable answer. Doing this afterwards would bake this
    # checkout's absolute path into the project.
    if args.embed:
        _do_embed(project, with_vendor=args.with_vendor, force=args.force,
                  verbose=args.verbose)
        print()

    result = inst.execute(plan, TOOLKIT_ROOT, force=args.force)
    rendered = result.report.render(project, verbose=args.verbose)
    if rendered:
        print(rendered)
    print()
    print(f"  {result.report.summary()}")

    conflicts = result.report.conflicts()
    if conflicts:
        print()
        print(yellow(bold(f"{len(conflicts)} conflict(s) - existing files were kept:")))
        for c in conflicts:
            print(f"  {c.path}  {dim(c.detail)}")
        print(dim("  re-run with --force to replace them"))

    if (result.ok and sys.platform == "win32" and not args.no_path
            and not args.embed and (TOOLKIT_ROOT / "bin" / "uat.cmd").is_file()
            and not inst.uat_on_path()):
        from .windows import add_to_user_path

        try:
            add_to_user_path(str(TOOLKIT_ROOT / "bin"))
            print(green("  uat is registered on your user PATH."))
            print(dim("  Restart your terminal application to use `uat`, or refresh $env:Path."))
            result.notes = [n for n in result.notes if "not on your PATH" not in n]
        except OSError as exc:
            print(yellow(f"  Could not update user PATH: {exc}"))

    if result.notes:
        print()
        print(bold("Manual steps required:"))
        for n in dict.fromkeys(result.notes):
            print(f"  - {n}")

    if (interactive and sys.platform != "win32" and not args.no_path
            and not args.embed and not inst.uat_on_path()):
        _offer_path_symlink(TOOLKIT_ROOT)

    print()
    print(green(bold("Installed.")) + " Next:")
    print(f"  1. read  {project}/.agent-toolkit/CORE.md")
    print(f"  2. start planning: point your agent at .agent-toolkit/workflow/README.md")
    return 0 if result.ok else 2


def _do_embed(project: Path, *, with_vendor: bool, force: bool, verbose: bool) -> None:
    """Copy the toolkit into the project's .agent-toolkit/toolkit/."""
    size = embedlib.estimate_size(TOOLKIT_ROOT, with_vendor=with_vendor)
    print(bold("Embedding the toolkit into the project"))
    print(f"  destination  .agent-toolkit/toolkit/")
    print(f"  vendored     {'yes - fully offline' if with_vendor else 'no'}")
    print(f"  adds         ~{embedlib.human(size)}")

    report = Report()
    dest = embedlib.embed(
        TOOLKIT_ROOT, project, with_vendor=with_vendor, force=force, report=report
    )
    if verbose:
        rendered = report.render(project, verbose=False)
        if rendered:
            print(rendered)
    print(f"  {report.summary()}")
    print()
    print("  this project can now manage itself:")
    print(cyan("    .agent-toolkit/toolkit/uat status --project ."))
    if not with_vendor:
        print(dim("  note: adding a NEW pack later needs `uat vendor sync` and network."))
        print(dim("        use --with-vendor to embed every upstream for offline use."))


def cmd_embed(args) -> int:
    project = _project(args)
    if not (project / inst.TOOLKIT_DIR).is_dir():
        raise ToolkitError(
            f"{project} has no .agent-toolkit/ yet. Run `uat install` first, "
            "or use `uat install --embed`."
        )
    _do_embed(project, with_vendor=args.with_vendor, force=args.force,
              verbose=args.verbose)
    return 0


# num, name, artifact it must produce (relative to project root), expects a report
PHASES = [
    ("00", "triage", "", False),          # triage announces a class; it writes no file
    ("01", "discovery", "", True),
    ("02", "business logic", "docs/business-logic.md", True),
    ("03", "screens & flows", "docs/screens.md", True),
    ("04", "stack", "docs/stack.md", True),
    ("05", "rules", "", True),
    ("06", "architecture", "docs/architecture.md", True),
    ("07", "content", "docs/content", True),
    ("08", "design", "docs/design", True),
    ("09", "environments", "", True),
    ("10", "plan", "docs/superpowers/plans", True),
    ("11", "GATE", "", True),
    ("12", "execute", "", True),
    ("13", "acceptance", "docs/acceptance.md", True),
]

# Template scaffolding that carries no information on its own.
_BOILERPLATE = re.compile(
    r"^\s*(#.*|[-*]\s*$|\|.*\||_.*_|<!--.*-->)?\s*$|"
    r"^\s*(TBD|TODO|\?\?\?|N/A|\[.*\])\s*$",
    re.IGNORECASE,
)


def report_substance(path: Path) -> tuple[str, int]:
    """Classify a phase report as 'done' or 'stub'.

    An empty file used to count as a completed phase, which is how a project
    reaches "all phases done" without anything having happened. Completion is
    judged on content, and even then only as evidence - never as proof.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "stub", 0
    meat = sum(
        len(line.strip())
        for line in text.splitlines()
        if line.strip() and not _BOILERPLATE.match(line)
    )
    return ("done" if meat >= 80 else "stub"), meat



def cmd_add_rule(args) -> int:
    """Install any vendored rule document, pack or no pack."""
    from .catalog import find_rule_document

    registry, _ = _load(TOOLKIT_ROOT)
    project = _project(args)
    if not (project / inst.TOOLKIT_DIR).is_dir():
        raise ToolkitError(f"no toolkit installed in {project}. Run `uat install` first.")

    vendor, rel, stem, src = find_rule_document(TOOLKIT_ROOT, args.rule)
    name = args.as_name or (stem.upper().replace("-", "_") + ".md")
    if not name.endswith(".md"):
        name += ".md"

    dest = project / inst.TOOLKIT_DIR / "rules" / name
    report = Report(dry_run=args.dry_run)
    from .util import copy_file
    copy_file(src, dest, force=args.force, report=report)

    if not args.dry_run and dest.is_file():
        inst.refresh(project, TOOLKIT_ROOT, registry, report=report)

    print(report.render(project, verbose=False) or dim("  no change"))
    print(f"\n  {report.summary()}")
    if report.conflicts():
        print(yellow("  a file of that name exists; use --as NAME.md or --force"))
        return 2
    print()
    print(f"  {green('installed')} {vendor}:{stem} -> .agent-toolkit/rules/{name}")
    print(dim("  this is community/vendored content - read it before relying on it"))
    return 0


def cmd_workflow(args) -> int:
    """Show how far the planning workflow has progressed."""
    project = _project(args)
    toolkit = project / inst.TOOLKIT_DIR
    if not toolkit.is_dir():
        raise ToolkitError(f"no toolkit installed in {project}")

    reports = toolkit / "reports"
    found: dict[str, Path] = {}
    if reports.is_dir():
        for f in reports.glob("*.md"):
            if f.name != "README.md" and f.name[:2].isdigit():
                found[f.name[:2]] = f

    doc = inst.read_json(toolkit / inst.PROJECT_FILE, default={})
    print(bold(f"Planning workflow: {project.name}"))
    print(f"  mode      {doc.get('mode', 'unknown')}")
    print(f"  agents    {', '.join(doc.get('agents', [])) or '-'}")
    print()

    next_phase = None
    stubs, missing_artifacts = [], []

    for num, name, artifact, expects in PHASES:
        report = found.get(num)
        state = "-"
        if not expects:
            state = "n/a"
        elif report is None:
            state = "todo"
        else:
            verdict, _ = report_substance(report)
            state = verdict
            if verdict == "stub":
                stubs.append(num)

        art_note = ""
        if artifact and state == "done":
            if not (project / artifact).exists():
                # A report claiming a phase is finished, without the artifact
                # that phase exists to produce, is not a finished phase.
                state = "gap"
                art_note = red(f"  missing {artifact}")
                missing_artifacts.append((num, artifact))
        elif artifact:
            art_note = dim(f"  -> {artifact}")

        if state in ("todo", "stub", "gap") and next_phase is None:
            mark, next_phase = yellow("next"), (num, name)
        elif state == "done":
            mark = green("done")
        elif state == "gap":
            mark = red(" gap")
        elif state == "n/a":
            mark = dim(" -- ")
        else:
            mark = dim("    ")

        label = bold(name) if num in ("11", "12") else name
        print(f"  {mark}  {num}  {label:<22}{art_note}")

    print()
    if stubs:
        print(yellow(f"  {len(stubs)} report(s) are stubs, not results: "
                     + ", ".join(stubs)))
    if missing_artifacts:
        print(red("  reports claim completion but the artifact is absent:"))
        for num, art in missing_artifacts:
            print(f"    {num} -> {art}")
    if not found:
        print("  nothing started yet.")
    elif next_phase is None:
        print(green("  every phase has a substantive report."))
        print(dim("  This is evidence, not proof. The gate (11) requires a human"))
        print(dim("  approval that no file can record - confirm it was given."))

    uat = f"./{inst.TOOLKIT_DIR}/toolkit/uat" \
        if (toolkit / "toolkit" / "uat").is_file() else "uat"

    print()
    print(bold("  To continue, give your agent:"))
    print(cyan(f"    Read {inst.TOOLKIT_DIR}/workflow/README.md and run the planning"))
    print(cyan("    workflow. Start with triage, tell me the classification and"))
    print(cyan("    which phases apply, then work through them in order. Stop at"))
    print(cyan("    the gate for my approval."))
    if (project / ".claude" / "commands" / "plan.md").is_file():
        print()
        print(dim("  Claude Code:  /plan <what to build>   /plan-status   /plan-resume"))
    if (toolkit / "START-HERE.md").is_file():
        print()
        print(dim(f"  Full guide:   {inst.TOOLKIT_DIR}/START-HERE.md"))
    print(dim(f"  Progress:     {uat} workflow --project ."))
    return 0


def cmd_status(args) -> int:
    registry, _ = _load(TOOLKIT_ROOT)
    project = _project(args)
    state = inst.load_state(project)
    if not state:
        print(red(f"no toolkit installation in {project}"))
        return 1

    print(bold(f"Toolkit status: {project}"))
    print(f"  installed   {state.get('installed_at')}")
    print(f"  version     {state.get('toolkit_version')}")
    print(f"  agents      {', '.join(state.get('agents', []))}")
    print(f"  packs       {len(state.get('packs', []))}")
    print(f"  skills      {state.get('skills_mode')}")

    modified, missing = inst.drift(project)
    print()
    if not modified and not missing:
        print(green("  no drift - installed files match the recorded install"))
    if modified:
        print(yellow(f"  {len(modified)} locally modified file(s):"))
        for m in modified[:20]:
            print(f"    ~ {m}")
        if len(modified) > 20:
            print(dim(f"    ... and {len(modified) - 20} more"))
        print(dim("    these will be kept unless you pass --force"))
    if missing:
        print(red(f"  {len(missing)} missing file(s):"))
        for m in missing[:20]:
            print(f"    - {m}")
    return 0


def cmd_uninstall(args) -> int:
    registry, _ = _load(TOOLKIT_ROOT)
    project = _project(args)
    report = Report(dry_run=args.dry_run)
    inst.uninstall(project, registry, report=report, keep_toolkit=args.keep_toolkit)
    print(report.render(project, verbose=True) or dim("  nothing to remove"))
    print(f"\n  {report.summary()}")
    if args.dry_run:
        print(dim("  (dry run)"))
    return 0


def cmd_vendor(args) -> int:
    ups = vendorlib.load_upstreams(TOOLKIT_ROOT)

    if args.vendor_cmd == "list":
        print(bold(f"{len(ups)} pinned upstreams"))
        for up in ups:
            ok, detail = vendorlib.verify_one(up, TOOLKIT_ROOT)
            mark = green("ok") if ok else red("!!")
            kind = cyan("local") if up.is_local else dim("git  ")
            print(f"  {mark} {kind} {up.id:<24} {up.short_ref:<8} "
                  f"{up.license[:24]:<26} {dim(detail)}")
        return 0

    if args.vendor_cmd == "verify":
        failed = 0
        for up in ups:
            ok, detail = vendorlib.verify_one(up, TOOLKIT_ROOT)
            print(f"  {green('ok') if ok else red('FAIL')} {up.id:<26} {detail}")
            failed += 0 if ok else 1
        print()
        if failed:
            print(red(bold(f"{failed} upstream(s) failed verification")))
            return 1
        print(green(bold("all vendored snapshots match their pins")))
        return 0

    if args.vendor_cmd == "add-local":
        vid, detail = vendorlib.add_local(
            TOOLKIT_ROOT, Path(args.path),
            vendor_id=args.id, license=args.license,
            notes=args.notes or "", force=args.force,
        )
        print(f"  {green('vendored')} {vid}  {dim(detail)}")
        print()
        print("  registered in catalog/vendor.json and content-hashed.")
        print("  Next: add a pack so it can be installed -")
        print(cyan(f"    catalog/packs/<id>/pack.json with a vendor_map for '{vid}'"))
        print(dim("  See docs/ARCHITECTURE.md for the pack format."))
        return 0

    # sync
    targets = [u for u in ups if not args.only or u.id in args.only]
    if not targets:
        raise ToolkitError(f"no upstream matches {args.only}")
    failed = 0
    for up in targets:
        print(f"  {up.id} ... ", end="", flush=True)
        try:
            status, detail = vendorlib.sync_one(up, TOOLKIT_ROOT, force=args.force)
            colour = {"synced": green, "unchanged": dim, "drifted": yellow}[status]
            print(colour(f"{status}  {detail}"))
        except ToolkitError as exc:
            failed += 1
            print(red(f"FAILED  {exc}"))
    return 1 if failed else 0


def cmd_doctor(args) -> int:
    problems: list[str] = []
    print(bold("Toolkit self-check"))

    try:
        registry, catalog = _load(TOOLKIT_ROOT)
        print(f"  {green('ok')}  registry: {len(registry)} agents")
        print(f"  {green('ok')}  catalog:  {len(catalog)} packs, {len(catalog.profiles)} profiles")
    except ToolkitError as exc:
        print(f"  {red('FAIL')}  {exc}")
        return 1

    slim = embedlib.is_embedded(TOOLKIT_ROOT) and not (TOOLKIT_ROOT / "vendor").exists()
    ups = vendorlib.load_upstreams(TOOLKIT_ROOT)
    if slim:
        info = embedlib.embed_info(TOOLKIT_ROOT)
        print(f"  {yellow('--')}  embedded copy v{info.get('toolkit_version', '?')} "
              f"without vendored upstreams")
        print(dim(f"      {len(ups)} upstream(s) not present; already-installed packs "
                  f"work offline, adding new ones needs `uat vendor sync`"))
    else:
        for up in ups:
            ok, detail = vendorlib.verify_one(up, TOOLKIT_ROOT)
            print(f"  {green('ok') if ok else red('FAIL')}  vendor {up.id}: {detail}")
            if not ok:
                problems.append(f"vendor {up.id}: {detail}")

    # every vendor_map target must exist
    if not slim:
        for pack in catalog:
            for vm in pack.vendor_maps:
                for rel in vm.required_paths():
                    if not (TOOLKIT_ROOT / "vendor" / vm.vendor / rel).exists():
                        problems.append(
                            f"pack {pack.id} -> missing vendor path {vm.vendor}/{rel}"
                        )

    if not slim:
        from .catalog import unreachable_vendor_content, unmapped_rule_files
        orphans = unreachable_vendor_content(catalog, TOOLKIT_ROOT)
        for vendor, names in orphans.items():
            problems.append(
                f"vendored but no pack can install it: {vendor} -> "
                + ", ".join(names)
            )
        if not orphans:
            print(f"  {green('ok')}  every vendored skill is reachable by a pack")
        unmapped = unmapped_rule_files(catalog, TOOLKIT_ROOT)
        for vendor, count in sorted(unmapped.items()):
            if count:
                print(dim(f"  --  {vendor}: {count} rule file(s) with no pack - reachable "
                          f"via `uat add-rule` (find them with `catalog --search`)"))

    declared = {u.id for u in ups}
    for present in vendorlib.vendored_ids(TOOLKIT_ROOT):
        if present not in declared:
            problems.append(
                f"vendor/{present} is not declared in catalog/vendor.json - it is "
                "ignored by sync, verify and every pack. Register it with "
                "`uat vendor add-local`, or delete it."
            )

    for name in ("catalog/core", "catalog/workflow"):
        if not (TOOLKIT_ROOT / name).exists():
            problems.append(f"missing {name}")

    print()
    if problems:
        print(red(bold(f"{len(problems)} problem(s):")))
        for p in problems:
            print(f"  - {p}")
        return 1
    print(green(bold("healthy")))
    return 0


# ----------------------------------------------------------------------
# parser
# ----------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="uat",
        description="Universal Agent Toolkit - install AI coding rules, skills and MCP "
                    "into a project, for the agents you actually use.",
    )
    p.add_argument("--verbose", "-v", action="store_true", help="show unchanged files too")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("agents", help="list supported coding agents")
    a.add_argument("--show", metavar="ID", help="show one agent's surfaces in detail")
    a.set_defaults(func=cmd_agents)

    c = sub.add_parser("catalog", help="list available packs and profiles")
    c.add_argument("--unmapped", action="store_true",
                   help="show vendored content that no pack exposes")
    c.add_argument("--search", metavar="TERM",
                   help="search every vendored rule document by name")
    c.set_defaults(func=cmd_catalog)

    d = sub.add_parser("detect", help="show what stack is detected in a project")
    d.add_argument("--project", default=".")
    d.set_defaults(func=cmd_detect)

    i = sub.add_parser("install", help="install the toolkit into a project")
    i.add_argument("--project", default=".", help="target project directory")
    i.add_argument(
        "--agent", action="append", default=[], metavar="ID",
        help="coding agent to configure; repeatable, or 'all'",
    )
    i.add_argument("--mode", choices=inst.MODES, help="interaction mode")
    i.add_argument("--profile", help="install a named profile")
    i.add_argument("--packs", nargs="*", metavar="ID", help="install exactly these packs")
    i.add_argument("--add", nargs="*", default=[], metavar="ID", help="add packs to the selection")
    i.add_argument("--all", action="store_true", help="install every pack")
    i.add_argument("--yes", "-y", action="store_true", help="no prompts")
    i.add_argument("--no-path", action="store_true",
                   help="skip Windows user PATH setup and Unix PATH prompt")
    i.add_argument("--force", action="store_true", help="replace conflicting files")
    i.add_argument("--dry-run", action="store_true", help="show what would change")
    i.add_argument("--copy", action="store_true", help="copy skills instead of symlinking")
    i.add_argument("--replace", action="store_true",
                   help="replace the recorded configuration instead of extending it "
                        "(drops packs and agents not named in this command)")
    i.add_argument("--embed", action="store_true",
                   help="also copy the toolkit into .agent-toolkit/toolkit/ so the "
                        "project can manage itself without this checkout")
    i.add_argument("--with-vendor", action="store_true",
                   help="with --embed, include every vendored upstream (fully offline, larger)")
    i.set_defaults(func=cmd_install)

    ar = sub.add_parser("add-rule",
                        help="install any vendored rule document, with or without a pack")
    ar.add_argument("rule", metavar="VENDOR:NAME",
                    help="e.g. awesome-copilot:wordpress (find it with catalog --search)")
    ar.add_argument("--project", default=".")
    ar.add_argument("--as", dest="as_name", metavar="NAME.md",
                    help="filename to install as (default: derived from the source)")
    ar.add_argument("--force", action="store_true")
    ar.add_argument("--dry-run", action="store_true")
    ar.set_defaults(func=cmd_add_rule)

    w = sub.add_parser("workflow", help="show planning workflow progress")
    w.add_argument("--project", default=".")
    w.set_defaults(func=cmd_workflow)

    s = sub.add_parser("status", help="show install state and local drift")
    s.add_argument("--project", default=".")
    s.set_defaults(func=cmd_status)

    u = sub.add_parser("uninstall", help="remove generated toolkit files")
    u.add_argument("--project", default=".")
    u.add_argument("--keep-toolkit", action="store_true", help="keep .agent-toolkit/")
    u.add_argument("--dry-run", action="store_true")
    u.set_defaults(func=cmd_uninstall)

    v = sub.add_parser("vendor", help="manage pinned upstream snapshots")
    vs = v.add_subparsers(dest="vendor_cmd", required=True)
    vl = vs.add_parser("list", help="list pins and verification state")
    vl.set_defaults(func=cmd_vendor)
    vv = vs.add_parser("verify", help="check snapshots match their pinned commits")
    vv.set_defaults(func=cmd_vendor)
    va = vs.add_parser("add-local",
                       help="vendor a local directory (your own or your company's rules)")
    va.add_argument("path", help="directory to snapshot into vendor/")
    va.add_argument("--id", required=True, help="vendor id, e.g. acme-house-rules")
    va.add_argument("--license", required=True,
                    help="licence or ownership note, e.g. 'Proprietary - ACME internal'")
    va.add_argument("--notes", help="what this is and where it came from")
    va.add_argument("--force", action="store_true", help="replace an existing snapshot")
    va.set_defaults(func=cmd_vendor)

    vy = vs.add_parser("sync", help="fetch upstreams at their pinned commits")
    vy.add_argument("--only", nargs="*", metavar="ID")
    vy.add_argument("--force", action="store_true", help="re-fetch even if unchanged")
    vy.set_defaults(func=cmd_vendor)

    e = sub.add_parser("embed",
                       help="copy the toolkit into an already-configured project")
    e.add_argument("--project", default=".")
    e.add_argument("--with-vendor", action="store_true",
                   help="include every vendored upstream (fully offline, larger)")
    e.add_argument("--force", action="store_true")
    e.set_defaults(func=cmd_embed)

    doc = sub.add_parser("doctor", help="self-check the toolkit repository")
    doc.set_defaults(func=cmd_doctor)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "cmd", None) == "install" and not args.agent:
        parser.error("install requires --agent (e.g. --agent claude-code, or --agent all)")
    try:
        return args.func(args)
    except ToolkitError as exc:
        print(red(f"error: {exc}"), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print()
        return 130
