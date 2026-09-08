#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "toolkit" / "manifest.json"
TEMPLATES = ROOT / "templates" / "project"

CORE_PACKS = {
    "superpowers", "karpathy-guidelines", "data-safety",
    "git-atomic", "security", "verification",
    "mcp-playwright", "mcp-context7",
}
FRONTEND_PACKS = {
    "ui-ux-pro-max", "figma-skills", "web-interface-guidelines",
    "mcp-figma",
}
REACT_PACKS = {"react-best-practices"}

MODES = {
    "1": ("thorough", "Thorough — ask all materially useful questions."),
    "2": ("focused", "Focused — ask only important/blocking questions; use sensible defaults."),
    "3": ("autonomous", "Autonomous — make reasonable decisions independently; ask only for blockers/high-impact actions."),
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        return default

def write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def detect_stack(project: Path) -> set[str]:
    found: set[str] = set()

    def text(rel: str) -> str:
        p = project / rel
        try:
            return p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    composer = {}
    cp = project / "composer.json"
    if cp.exists():
        found.add("php")
        try:
            composer = json.loads(cp.read_text(encoding="utf-8"))
        except Exception:
            composer = {}
        deps = {}
        deps.update(composer.get("require", {}) or {})
        deps.update(composer.get("require-dev", {}) or {})
        if "laravel/framework" in deps:
            found.add("laravel")
        if any(k.startswith("symfony/") for k in deps):
            found.add("symfony")

    package = {}
    pp = project / "package.json"
    if pp.exists():
        found.update({"javascript", "node"})
        try:
            package = json.loads(pp.read_text(encoding="utf-8"))
        except Exception:
            package = {}
        deps = {}
        deps.update(package.get("dependencies", {}) or {})
        deps.update(package.get("devDependencies", {}) or {})
        if "typescript" in deps:
            found.add("typescript")
        if "react" in deps:
            found.update({"react", "frontend"})
        if "next" in deps:
            found.update({"nextjs", "react", "frontend"})
        if "vue" in deps:
            found.update({"vue", "frontend"})
        if "tailwindcss" in deps or "@tailwindcss/postcss" in deps:
            found.update({"tailwind", "frontend"})
        if "@nestjs/core" in deps:
            found.add("nestjs")

    if (project / "tsconfig.json").exists():
        found.add("typescript")
    if any((project / x).exists() for x in ["vite.config.ts","vite.config.js","next.config.js","next.config.mjs","next.config.ts"]):
        found.add("frontend")

    py_files = [project/"pyproject.toml", project/"requirements.txt", project/"Pipfile"]
    if any(p.exists() for p in py_files):
        found.add("python")
        blob = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in py_files if p.exists()).lower()
        if "fastapi" in blob:
            found.add("fastapi")
        if "django" in blob:
            found.add("django")

    if (project / "go.mod").exists():
        found.add("go")
    if (project / "Cargo.toml").exists():
        found.add("rust")
    if list(project.glob("*.csproj")) or list(project.rglob("*.csproj"))[:1]:
        found.add("dotnet")
    if (project/"pom.xml").exists() or (project/"build.gradle").exists() or (project/"build.gradle.kts").exists():
        found.add("java")
        blob = (text("pom.xml") + text("build.gradle") + text("build.gradle.kts")).lower()
        if "spring" in blob:
            found.add("spring")

    infra_names = ["compose.yml","compose.yaml","docker-compose.yml","docker-compose.yaml","Dockerfile"]
    infra_blob = "\n".join(text(x) for x in infra_names if (project/x).exists()).lower()
    if infra_blob:
        found.add("docker")
    if "postgres" in infra_blob or "postgresql" in infra_blob:
        found.add("postgresql")
    if "mysql" in infra_blob or "mariadb" in infra_blob:
        found.add("mysql")
    if "redis" in infra_blob:
        found.add("redis")
    if "nginx" in infra_blob or list(project.rglob("*nginx*.conf"))[:1]:
        found.add("nginx")

    # Existing design/frontend hints
    if any((project / x).exists() for x in ["src","app","pages"]) and package:
        found.add("frontend")

    return found

def choose_mode(project: Path, noninteractive: bool, requested: str | None, reconfigure: bool) -> str:
    state_path = project / ".agent-toolkit" / "project.json"
    existing = load_json(state_path, {})
    if requested:
        return requested
    if existing.get("interaction_mode") and not reconfigure:
        return existing["interaction_mode"]
    if noninteractive:
        return "focused"

    print("\nHow should the agent handle clarifying questions?")
    print("  1) Thorough   — ask all materially useful questions")
    print("  2) Focused    — ask only important/blocking questions (default)")
    print("  3) Autonomous — decide independently; interrupt only for blockers/high-impact actions")
    while True:
        answer = input("Choose [1/2/3, default 2]: ").strip() or "2"
        if answer in MODES:
            return MODES[answer][0]
        print("Please choose 1, 2, or 3.")

def default_selection(packs: list[dict], detected: set[str], profile: set[str] | None, all_items: bool) -> set[str]:
    if all_items:
        return {p["id"] for p in packs}
    if profile is not None:
        return set(profile)

    selected = {p["id"] for p in packs if p.get("default")}
    for p in packs:
        if set(p.get("detect", [])) & detected:
            selected.add(p["id"])

    if "frontend" in detected:
        selected |= FRONTEND_PACKS
    if "react" in detected or "nextjs" in detected:
        selected |= REACT_PACKS
    return selected

def installed_state(project: Path) -> dict:
    return load_json(project / ".agent-toolkit" / "installed.json", {"packs": {}})

def is_pack_installed(project: Path, pack_id: str, state: dict) -> bool:
    record = (state.get("packs") or {}).get(pack_id)
    if record:
        return True
    source = ROOT / "toolkit" / "packs" / pack_id / "files"
    if not source.exists():
        return False
    files = [p for p in source.rglob("*") if p.is_file()]
    if not files:
        return False
    return all((project / p.relative_to(source)).exists() for p in files)

def render_checklist(packs: list[dict], selected: set[str], project: Path, state: dict, detected: set[str]):
    print("\nDetected stack:", ", ".join(sorted(detected)) if detected else "none / new project")
    print("\nSkills & Rules")
    index = {}
    n = 1
    for kind in ("skill","rule"):
        for p in packs:
            if p["kind"] != kind:
                continue
            index[n] = p
            installed = is_pack_installed(project, p["id"], state)
            check = "x" if p["id"] in selected else " "
            status = "✓ installed — skip" if installed else ""
            reason = ""
            if p.get("default"):
                reason = "core"
            elif set(p.get("detect", [])) & detected:
                reason = "detected: " + ",".join(sorted(set(p.get("detect", [])) & detected))
            elif "frontend" in p.get("tags", []) and "frontend" in detected:
                reason = "frontend"
            label = f"{n:>3} [{check}] {p['label']:<32}"
            print(f"{label} {reason:<20} {status}")
            n += 1

    print("\nMCP")
    for p in packs:
        if p["kind"] != "mcp":
            continue
        index[n] = p
        installed = is_pack_installed(project, p["id"], state)
        check = "x" if p["id"] in selected else " "
        status = "✓ installed — skip" if installed else ""
        reason = "core" if p.get("default") else ("frontend" if "frontend" in p.get("tags", []) and "frontend" in detected else "optional")
        label = f"{n:>3} [{check}] {p['label']:<32}"
        print(f"{label} {reason:<20} {status}")
        n += 1
    return index

def interactive_select(packs: list[dict], selected: set[str], project: Path, state: dict, detected: set[str], recommended: set[str]) -> set[str]:
    while True:
        index = render_checklist(packs, selected, project, state, detected)
        print("\nToggle: numbers/comma/ranges (e.g. 6,8-10) | a=all | n=none | r=recommended | Enter=install")
        answer = input("> ").strip().lower()
        if not answer:
            return selected
        if answer == "a":
            selected = {p["id"] for p in packs}
            continue
        if answer == "n":
            selected = set()
            continue
        if answer == "r":
            selected = set(recommended)
            continue

        nums: set[int] = set()
        ok = True
        for token in re.split(r"\s*,\s*", answer):
            if not token:
                continue
            if "-" in token:
                try:
                    a,b = [int(x) for x in token.split("-",1)]
                    nums.update(range(min(a,b), max(a,b)+1))
                except Exception:
                    ok=False
            else:
                try:
                    nums.add(int(token))
                except Exception:
                    ok=False
        if not ok or any(x not in index for x in nums):
            print("Invalid selection.")
            continue
        for x in nums:
            pid=index[x]["id"]
            if pid in selected:
                selected.remove(pid)
            else:
                selected.add(pid)

def copy_file(src: Path, dst: Path, force: bool, dry_run: bool, report: list[str]) -> str:
    if dst.exists():
        try:
            if src.is_file() and sha256(src) == sha256(dst):
                report.append(f"SKIP same: {dst}")
                return "same"
        except Exception:
            pass
        if not force:
            report.append(f"CONFLICT kept existing: {dst}")
            return "conflict"
        report.append(f"OVERWRITE (--force): {dst}")
    else:
        report.append(f"ADD: {dst}")

    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return "copied"

def copy_tree(src_root: Path, project: Path, force: bool, dry_run: bool, report: list[str]):
    if not src_root.exists():
        return
    for src in sorted(p for p in src_root.rglob("*") if p.is_file()):
        dst = project / src.relative_to(src_root)
        copy_file(src,dst,force,dry_run,report)

def write_text_safe(dst: Path, content: str, force: bool, dry_run: bool, report: list[str]):
    if dst.exists():
        existing = dst.read_text(encoding="utf-8", errors="ignore")
        if existing == content:
            report.append(f"SKIP same: {dst}")
            return
        if not force:
            report.append(f"CONFLICT kept existing: {dst}")
            return
        report.append(f"OVERWRITE (--force): {dst}")
    else:
        report.append(f"ADD: {dst}")
    if not dry_run:
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(content,encoding="utf-8")

def install_bridges(project: Path, force: bool, dry_run: bool, report: list[str]):
    for src in sorted(p for p in TEMPLATES.rglob("*") if p.is_file()):
        dst = project / src.relative_to(TEMPLATES)
        copy_file(src,dst,force,dry_run,report)

def build_core(mode: str) -> str:
    parts = [
        "# Project AI Control Plane\n",
        f"Interaction mode: **{mode}**.\n",
        "Read and apply the sections below. Project-specific requirements and direct human instructions override this generic toolkit.\n",
        (ROOT/"toolkit/core/INTERACTION_MODES.md").read_text(),
        (ROOT/"toolkit/core/PROJECT_WORKFLOW.md").read_text(),
        (ROOT/"toolkit/core/DATA_SAFETY.md").read_text(),
        (ROOT/"toolkit/core/GIT.md").read_text(),
        (ROOT/"toolkit/core/SECURITY.md").read_text(),
        (ROOT/"toolkit/core/VERIFICATION.md").read_text(),
    ]
    return "\n\n---\n\n".join(parts)

def mirror_skills(project: Path, force: bool, dry_run: bool, report: list[str]):
    canonical = project / ".agents" / "skills"
    if not canonical.exists():
        return
    # Claude and Gemini still benefit from explicit native project skill folders.
    for tool_dir in [project/".claude"/"skills", project/".gemini"/"skills"]:
        for skill_dir in sorted(p for p in canonical.iterdir() if p.is_dir()):
            for src in sorted(p for p in skill_dir.rglob("*") if p.is_file()):
                dst = tool_dir / skill_dir.name / src.relative_to(skill_dir)
                copy_file(src,dst,force,dry_run,report)

def mcp_specs(project: Path, selected: set[str]) -> dict[str,dict]:
    specs={}
    for pid in selected:
        if not pid.startswith("mcp-"):
            continue
        src = ROOT/"toolkit"/"packs"/pid/"files"/".agent-toolkit"/"mcp"
        if not src.exists():
            continue
        for f in src.glob("*.json"):
            try:
                spec=json.loads(f.read_text())
                specs[spec["name"]]=spec
            except Exception:
                pass
    return specs

def stdio_entry(project: Path, spec: dict, style: str) -> dict:
    # Use project-relative path where supported.
    rel = spec["command_rel"]
    if style == "vscode":
        cmd = "${workspaceFolder}/" + rel
    else:
        cmd = "./" + rel
    return {"command": cmd, "args": spec.get("args", [])}

def merge_json_config(path: Path, root_key: str, servers: dict[str,dict], force: bool, dry_run: bool, report: list[str], base: dict|None=None):
    if path.exists():
        try:
            obj=json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            report.append(f"CONFLICT invalid/non-JSON existing config: {path}")
            return
    else:
        obj=base.copy() if base else {}
    bucket=obj.setdefault(root_key,{})
    changed=False
    for name,entry in servers.items():
        if name in bucket:
            if bucket[name] == entry:
                report.append(f"SKIP MCP same {name}: {path}")
                continue
            if not force:
                report.append(f"CONFLICT MCP kept existing {name}: {path}")
                continue
        bucket[name]=entry
        changed=True
        report.append(f"{'UPDATE' if path.exists() else 'ADD'} MCP {name}: {path}")
    if changed and not dry_run:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")

def install_mcp_configs(project: Path, selected: set[str], force: bool, dry_run: bool, report: list[str]):
    specs=mcp_specs(project,selected)
    if not specs:
        return

    claude={}
    vscode={}
    gemini={}
    for name,s in specs.items():
        if s.get("transport") == "stdio":
            claude[name]=stdio_entry(project,s,"generic")
            vscode[name]={"type":"stdio", **stdio_entry(project,s,"vscode")}
            gemini[name]=stdio_entry(project,s,"generic")
        elif s.get("transport") == "http":
            claude[name]={"type":"http","url":s["url"]}
            vscode[name]={"type":"http","url":s["url"]}
            gemini[name]={"httpUrl":s["url"]}

    # Claude Code project config
    merge_json_config(project/".mcp.json","mcpServers",claude,force,dry_run,report)
    # Cursor
    merge_json_config(project/".cursor"/"mcp.json","mcpServers",claude,force,dry_run,report)
    # VS Code / Copilot
    merge_json_config(project/".vscode"/"mcp.json","servers",vscode,force,dry_run,report,base={"inputs":[]})
    # Gemini CLI
    merge_json_config(project/".gemini"/"settings.json","mcpServers",gemini,force,dry_run,report)

    # Codex project TOML: add only missing server blocks. Preserve existing content.
    codex_path=project/".codex"/"config.toml"
    existing=codex_path.read_text(encoding="utf-8",errors="ignore") if codex_path.exists() else ""
    additions=[]
    for name,s in specs.items():
        marker=f"[mcp_servers.{name}]"
        if marker in existing:
            report.append(f"SKIP MCP existing {name}: {codex_path}")
            continue
        if s.get("transport")=="stdio":
            cmd="./"+s["command_rel"]
            additions.append(f'{marker}\ncommand = "{cmd}"\nargs = {json.dumps(s.get("args",[]))}\n')
        elif s.get("transport")=="http":
            additions.append(f'{marker}\nurl = "{s["url"]}"\n')
    if additions:
        report.append(f"{'UPDATE' if codex_path.exists() else 'ADD'} MCP blocks: {codex_path}")
        if not dry_run:
            codex_path.parent.mkdir(parents=True,exist_ok=True)
            prefix=existing.rstrip()
            content=(prefix+"\n\n" if prefix else "")+"\n".join(additions).rstrip()+"\n"
            codex_path.write_text(content,encoding="utf-8")

def main():
    ap=argparse.ArgumentParser(description="Install selected Universal Agent Toolkit resources into a project.")
    ap.add_argument("--project", default=".", help="Target project directory")
    ap.add_argument("--yes", action="store_true", help="Non-interactive; accept recommended selection")
    ap.add_argument("--all", action="store_true", help="Select all packs")
    ap.add_argument("--profile", help="Profile name from profiles/<name>.json")
    ap.add_argument("--force", action="store_true", help="Explicitly overwrite conflicting toolkit-managed files")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--mode", choices=["thorough","focused","autonomous"])
    ap.add_argument("--reconfigure", action="store_true", help="Ask/change interaction mode even if already recorded")
    ap.add_argument("--no-mcp-config", action="store_true", help="Copy MCP pack metadata but do not generate tool MCP configs")
    args=ap.parse_args()

    project=Path(args.project).expanduser().resolve()
    project.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(MANIFEST_PATH.read_text())
    packs=manifest["packs"]

    detected=detect_stack(project)
    mode=choose_mode(project,args.yes,args.mode,args.reconfigure)

    profile_set=None
    if args.profile:
        pf=ROOT/"profiles"/f"{args.profile}.json"
        if not pf.exists():
            raise SystemExit(f"Unknown profile: {args.profile}")
        profile_set=set(json.loads(pf.read_text())["packs"])

    recommended=default_selection(packs,detected,profile_set,args.all)
    selected=set(recommended)
    state=installed_state(project)

    if not args.yes and not args.all and profile_set is None:
        selected=interactive_select(packs,selected,project,state,detected,recommended)

    print("\nSelected:", ", ".join(sorted(selected)) if selected else "(none)")
    if args.dry_run:
        print("Dry run: no files will be changed.")

    report=[]
    # Tool bridges and canonical control plane
    install_bridges(project,args.force,args.dry_run,report)
    core_content=build_core(mode)
    write_text_safe(project/".agent-toolkit"/"CORE.md",core_content,args.force,args.dry_run,report)

    # Install selected packs
    pack_by_id={p["id"]:p for p in packs}
    new_state=state if isinstance(state,dict) else {"packs":{}}
    new_state.setdefault("packs",{})
    for pid in sorted(selected):
        if pid not in pack_by_id:
            report.append(f"UNKNOWN pack skipped: {pid}")
            continue
        src=ROOT/"toolkit"/"packs"/pid/"files"
        if not src.exists():
            report.append(f"MISSING pack source: {pid}")
            continue
        copy_tree(src,project,args.force,args.dry_run,report)
        if not args.dry_run:
            new_state["packs"][pid]={
                "kind":pack_by_id[pid]["kind"],
                "version":pack_by_id[pid].get("version"),
                "source":pack_by_id[pid].get("source"),
            }

    mirror_skills(project,args.force,args.dry_run,report)

    if not args.no_mcp_config:
        install_mcp_configs(project,selected,args.force,args.dry_run,report)

    if not args.dry_run:
        write_json(project/".agent-toolkit"/"project.json", {
            "interaction_mode":mode,
            "detected_stack":sorted(detected),
            "selected_packs":sorted(selected),
        })
        write_json(project/".agent-toolkit"/"installed.json",new_state)
        reports=project/".agent-toolkit"/"reports"
        reports.mkdir(parents=True,exist_ok=True)
        (reports/"00-bootstrap.md").write_text(
            "# Step 0 — Toolkit Bootstrap\n\n"
            "## Detected stack\n" + (", ".join(sorted(detected)) or "None / new project") + "\n\n"
            f"## Interaction mode\n{mode}\n\n"
            "## Selected packs\n" + "\n".join(f"- {x}" for x in sorted(selected)) + "\n\n"
            "## File actions\n```text\n" + "\n".join(report) + "\n```\n",
            encoding="utf-8"
        )

    print("\nActions")
    for line in report:
        print(" ",line)

    conflicts=sum(1 for x in report if x.startswith("CONFLICT"))
    if conflicts:
        print(f"\n{conflicts} conflict(s) preserved. Re-run with --force only if overwrite is intentional.")
    print("\nBootstrap complete." if not args.dry_run else "\nDry run complete.")

if __name__=="__main__":
    main()
