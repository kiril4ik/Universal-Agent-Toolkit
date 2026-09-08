"""Embedding: put the toolkit itself inside the project it configures.

Two ways to use this toolkit:

  external  the toolkit lives somewhere else and installs into projects.
            Projects stay small; re-running `uat` needs that checkout.

  embedded  the toolkit is copied into <project>/.agent-toolkit/toolkit/.
            The project is self-contained and portable - it carries the CLI,
            the catalog, and optionally every vendored upstream, so it can
            add packs later with no external dependency.

Embedding never adds a folder to the project root. Everything lands inside
the single `.agent-toolkit/` directory the project already has.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

from .util import Report, copy_file, copy_tree, dumps_json, iter_files, write_text

TOOLKIT_DIR = ".agent-toolkit"
EMBED_DIR = "toolkit"
MARKER = "EMBEDDED.json"

# The launcher used inside a project. Unlike bin/uat it treats its own
# directory as the toolkit root, because the embedded layout has no bin/.
LAUNCHER = """#!/usr/bin/env bash
# Universal Agent Toolkit - embedded copy.
# Run from anywhere:  <project>/.agent-toolkit/toolkit/uat <command>
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1; then
    exec "$py" -c 'import sys; sys.path.insert(0, sys.argv[1]); \
from uat.cli import main; sys.exit(main(sys.argv[2:]))' "$here/src" "$@"
  fi
done

echo "uat: python3 is required but was not found on PATH" >&2
exit 1
"""

README = """# Embedded toolkit

This is a copy of the Universal Agent Toolkit, living inside the project it
configures. It exists so this project stays self-contained: no external
checkout is needed to change its agent configuration.

## Use it

```bash
.agent-toolkit/toolkit/uat status  --project .
.agent-toolkit/toolkit/uat catalog
.agent-toolkit/toolkit/uat install --project . --agent claude-code --add go
```

## What is here

```
toolkit/
  uat          launcher (no install step, python3 only)
  src/uat/     implementation
  catalog/     agent registry, packs, profiles, core policy, workflow
  vendor/      pinned upstream snapshots{vendor_note}
```

## Updating

This copy is pinned to toolkit version {version}. To update it, re-run
`uat embed` from a newer checkout of the toolkit repository. Nothing here is
fetched automatically.

Do not edit `vendor/` - `uat vendor verify` checks it against recorded content
hashes and will fail.
"""

# Toolkit paths that are never embedded: they serve the factory, not projects.
SKIP_TOP = {".git", ".github", "tests", "docs", "bin", "__pycache__", ".gitignore"}


def embed(
    toolkit_root: Path,
    project: Path,
    *,
    with_vendor: bool,
    force: bool,
    report: Report,
) -> Path:
    """Copy the toolkit into <project>/.agent-toolkit/toolkit/."""
    dest = project / TOOLKIT_DIR / EMBED_DIR

    # implementation + catalog: always
    copy_tree(toolkit_root / "src", dest / "src", force=force, report=report)
    copy_tree(toolkit_root / "catalog", dest / "catalog", force=force, report=report)

    for name in ("VERSION", "LICENSE"):
        src = toolkit_root / name
        if src.is_file():
            copy_file(src, dest / name, force=force, report=report)

    # vendored upstreams: optional, and the bulk of the size
    vendor_files = 0
    if with_vendor:
        vsrc = toolkit_root / "vendor"
        if vsrc.exists():
            copy_tree(vsrc, dest / "vendor", force=force, report=report)
            vendor_files = sum(1 for _ in iter_files(vsrc))

    write_text(dest / "uat", LAUNCHER, force=True, report=report)
    if not report.dry_run:
        (dest / "uat").chmod(0o755)

    version = _version(toolkit_root)
    write_text(
        dest / "README.md",
        README.format(
            version=version,
            vendor_note="" if with_vendor else "  (NOT embedded - see below)",
        ),
        force=True,
        report=report,
    )

    write_text(
        dest / MARKER,
        dumps_json(
            {
                "toolkit_version": version,
                "embedded_at": _dt.datetime.now(_dt.timezone.utc)
                .replace(microsecond=0)
                .isoformat(),
                "with_vendor": with_vendor,
                "vendor_files": vendor_files,
                "source": str(toolkit_root),
                "_note": (
                    "This project carries its own copy of the toolkit. "
                    "Run .agent-toolkit/toolkit/uat from the project root."
                    if with_vendor
                    else "Vendored upstreams were not embedded: installing a NEW "
                    "pack needs `uat vendor sync` and network access. "
                    "Packs already installed work offline."
                ),
            }
        ),
        force=True,
        report=report,
    )
    return dest


def is_embedded(toolkit_root: Path) -> bool:
    return (toolkit_root / MARKER).is_file()


def embed_info(toolkit_root: Path) -> dict:
    from .util import read_json

    return read_json(toolkit_root / MARKER, default={})


def _version(toolkit_root: Path) -> str:
    vf = toolkit_root / "VERSION"
    return vf.read_text(encoding="utf-8").strip() if vf.is_file() else "0.0.0-dev"


def estimate_size(toolkit_root: Path, *, with_vendor: bool) -> int:
    """Bytes that embedding would add, so the CLI can warn before copying."""
    total = 0
    for sub in ("src", "catalog"):
        for f in iter_files(toolkit_root / sub):
            total += f.stat().st_size
    if with_vendor:
        for f in iter_files(toolkit_root / "vendor"):
            total += f.stat().st_size
    return total


def human(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} GB"
