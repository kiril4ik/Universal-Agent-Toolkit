"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
    """Numbered toggle list. Returns the final selection."""
    selected = set(recommended)
    items = list(catalog)

    while True:
        print()
        print(bold("Select packs to install"))
        print(dim("  toggle: numbers/ranges (1 3 5-8)   a=all  n=none  r=reset  Enter=accept"))
        print()
        last_tier = None
        for idx, pack in enumerate(items, 1):
            if pack.tier != last_tier:
                print(f"  {bold(pack.tier.upper())}")
                last_tier = pack.tier
            mark = green("x") if pack.id in selected else " "
            why = ""
            if pack.detect and (set(pack.detect) & detection.tokens):
                hit = sorted(set(pack.detect) & detection.tokens)[0]
                why = dim(f"  detected: {hit}")
            elif pack.tier == "core":
                why = dim("  always")
            print(f"   {idx:>3} [{mark}] {pack.title:<34}{why}")
        print()

        try:
            answer = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            raise ToolkitError("cancelled")

        if answer == "":
            return catalog.expand(selected)
        if answer == "a":
            selected = set(catalog.ids)
            continue
        if answer == "n":
            selected = set()
            continue
        if answer == "r":
            selected = set(recommended)
            continue

        wanted: set[int] = set()
        bad = False
        for tok in answer.replace(",", " ").split():
            if "-" in tok:
                a, _, b = tok.partition("-")
                if a.isdigit() and b.isdigit():
                    wanted.update(range(int(a), int(b) + 1))
                else:
                    bad = True
            elif tok.isdigit():
                wanted.add(int(tok))
            else:
                bad = True
        if bad or any(n < 1 or n > len(items) for n in wanted):
            print(red("  invalid selection"))
            continue
        for n in wanted:
            pid = items[n - 1].id
            selected.symmetric_difference_update({pid})


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


def cmd_install(args) -> int:
    registry, catalog = _load(TOOLKIT_ROOT)
    project = _project(args)

    interactive = sys.stdin.isatty() and not args.yes and not args.dry_run

    mode = args.mode
    if mode is None:
        mode = _choose_mode() if interactive else "focused"

    detection, recommended = _resolve_selection(args, registry, catalog, project)

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

    if result.notes:
        print()
        print(bold("Manual steps required:"))
        for n in dict.fromkeys(result.notes):
            print(f"  - {n}")

    print()
    print(green(bold("Installed.")) + " Next:")
    print(f"  1. read  {project}/.agent-toolkit/CORE.md")
    print(f"  2. start planning: point your agent at .agent-toolkit/workflow/README.md")
    return 0 if result.ok else 2


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
            print(f"  {mark} {up.id:<26} {up.short_ref}  {up.license:<12} {dim(detail)}")
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

    ups = vendorlib.load_upstreams(TOOLKIT_ROOT)
    for up in ups:
        ok, detail = vendorlib.verify_one(up, TOOLKIT_ROOT)
        print(f"  {green('ok') if ok else red('FAIL')}  vendor {up.id}: {detail}")
        if not ok:
            problems.append(f"vendor {up.id}: {detail}")

    # every vendor_map target must exist
    for pack in catalog:
        for vm in pack.vendor_maps:
            for rel in vm.required_paths():
                if not (TOOLKIT_ROOT / "vendor" / vm.vendor / rel).exists():
                    problems.append(
                        f"pack {pack.id} -> missing vendor path {vm.vendor}/{rel}"
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
    i.add_argument("--force", action="store_true", help="replace conflicting files")
    i.add_argument("--dry-run", action="store_true", help="show what would change")
    i.add_argument("--copy", action="store_true", help="copy skills instead of symlinking")
    i.set_defaults(func=cmd_install)

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
    vy = vs.add_parser("sync", help="fetch upstreams at their pinned commits")
    vy.add_argument("--only", nargs="*", metavar="ID")
    vy.add_argument("--force", action="store_true", help="re-fetch even if unchanged")
    vy.set_defaults(func=cmd_vendor)

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
