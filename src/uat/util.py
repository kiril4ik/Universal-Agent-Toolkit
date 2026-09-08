"""Filesystem, hashing and reporting helpers.

Every mutating helper routes through Action/Report so that --dry-run is
honoured in exactly one place and the installer can never silently
clobber a file.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


class ToolkitError(Exception):
    """User-facing error. The CLI prints these without a traceback."""


# --------------------------------------------------------------------------
# terminal output
# --------------------------------------------------------------------------

def _supports_colour() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("UAT_FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


_C = _supports_colour()


def paint(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _C else text


def bold(t: str) -> str:
    return paint(t, "1")


def dim(t: str) -> str:
    return paint(t, "2")


def green(t: str) -> str:
    return paint(t, "32")


def yellow(t: str) -> str:
    return paint(t, "33")


def red(t: str) -> str:
    return paint(t, "31")


def cyan(t: str) -> str:
    return paint(t, "36")


# --------------------------------------------------------------------------
# hashing
# --------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_tree(root: Path) -> str:
    """Stable hash of a directory: covers relative paths and contents."""
    h = hashlib.sha256()
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        h.update(str(p.relative_to(root)).replace(os.sep, "/").encode())
        h.update(sha256_file(p).encode())
    return h.hexdigest()


# --------------------------------------------------------------------------
# json
# --------------------------------------------------------------------------

def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        if default is None:
            raise ToolkitError(f"missing required file: {path}")
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ToolkitError(f"invalid JSON in {path}: {exc}") from exc


def dumps_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------
# change reporting
# --------------------------------------------------------------------------

ADD = "add"
SAME = "same"
CONFLICT = "conflict"
OVERWRITE = "overwrite"
LINK = "link"
SKIP = "skip"

_SYMBOL = {
    ADD: (green("+"), "added"),
    SAME: (dim("="), "unchanged"),
    CONFLICT: (yellow("!"), "kept existing"),
    OVERWRITE: (yellow("~"), "overwritten"),
    LINK: (green(">"), "linked"),
    SKIP: (dim("-"), "skipped"),
}


@dataclass
class Action:
    kind: str
    path: str
    detail: str = ""


@dataclass
class Report:
    actions: list[Action] = field(default_factory=list)
    dry_run: bool = False

    def record(self, kind: str, path: Path | str, detail: str = "") -> str:
        self.actions.append(Action(kind, str(path), detail))
        return kind

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for a in self.actions:
            out[a.kind] = out.get(a.kind, 0) + 1
        return out

    def conflicts(self) -> list[Action]:
        return [a for a in self.actions if a.kind == CONFLICT]

    def render(self, base: Path, verbose: bool = False) -> str:
        lines: list[str] = []
        for a in self.actions:
            if not verbose and a.kind == SAME:
                continue
            sym, _ = _SYMBOL.get(a.kind, ("?", a.kind))
            try:
                shown = Path(a.path).relative_to(base)
            except ValueError:
                shown = Path(a.path)
            suffix = f"  {dim(a.detail)}" if a.detail else ""
            lines.append(f"  {sym} {shown}{suffix}")
        return "\n".join(lines)

    def summary(self) -> str:
        c = self.counts()
        bits = []
        for kind in (ADD, LINK, OVERWRITE, SAME, CONFLICT, SKIP):
            if c.get(kind):
                bits.append(f"{c[kind]} {_SYMBOL[kind][1]}")
        return ", ".join(bits) if bits else "nothing to do"


# --------------------------------------------------------------------------
# safe writes
# --------------------------------------------------------------------------

def write_text(dst: Path, content: str, *, force: bool, report: Report) -> str:
    """Write text, never overwriting divergent content unless force=True."""
    if dst.exists() or dst.is_symlink():
        if dst.is_symlink():
            return report.record(CONFLICT, dst, "exists as a symlink")
        existing = dst.read_text(encoding="utf-8", errors="replace")
        if existing == content:
            return report.record(SAME, dst)
        if not force:
            return report.record(CONFLICT, dst, "differs; use --force to replace")
        kind = OVERWRITE
    else:
        kind = ADD

    if not report.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content, encoding="utf-8")
    return report.record(kind, dst)


def copy_file(src: Path, dst: Path, *, force: bool, report: Report) -> str:
    if dst.exists() or dst.is_symlink():
        if dst.is_symlink():
            return report.record(CONFLICT, dst, "exists as a symlink")
        if sha256_file(src) == sha256_file(dst):
            return report.record(SAME, dst)
        if not force:
            return report.record(CONFLICT, dst, "differs; use --force to replace")
        kind = OVERWRITE
    else:
        kind = ADD

    if not report.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return report.record(kind, dst)


def copy_tree(src_root: Path, dst_root: Path, *, force: bool, report: Report) -> None:
    if not src_root.exists():
        return
    for src in sorted(p for p in src_root.rglob("*") if p.is_file()):
        copy_file(src, dst_root / src.relative_to(src_root), force=force, report=report)


def link_or_copy(src_dir: Path, dst: Path, *, mode: str, force: bool, report: Report) -> str:
    """Point `dst` at `src_dir`.

    mode="link" creates a relative symlink (no duplication on disk).
    mode="copy" mirrors the tree, for Windows or filesystems without symlinks.
    """
    if mode == "copy":
        copy_tree(src_dir, dst, force=force, report=report)
        return ADD

    rel = os.path.relpath(src_dir, dst.parent)

    if dst.is_symlink():
        if os.readlink(dst) == rel:
            return report.record(SAME, dst, f"-> {rel}")
        if not force:
            return report.record(CONFLICT, dst, f"symlink points elsewhere ({os.readlink(dst)})")
        if not report.dry_run:
            dst.unlink()
    elif dst.exists():
        if not force:
            return report.record(CONFLICT, dst, "real directory exists; use --copy or --force")
        if not report.dry_run:
            shutil.rmtree(dst) if dst.is_dir() else dst.unlink()

    if not report.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(rel, dst, target_is_directory=True)
        except OSError as exc:
            # Windows without developer mode, or a filesystem that refuses links.
            report.record(SKIP, dst, f"symlink unsupported ({exc.strerror}); copying instead")
            copy_tree(src_dir, dst, force=force, report=report)
            return ADD
    return report.record(LINK, dst, f"-> {rel}")


def supports_symlinks(probe_dir: Path) -> bool:
    """Empirically check symlink support rather than guessing from platform."""
    probe_dir.mkdir(parents=True, exist_ok=True)
    target = probe_dir / ".uat-symlink-probe-target"
    link = probe_dir / ".uat-symlink-probe-link"
    try:
        target.mkdir(exist_ok=True)
        if link.is_symlink() or link.exists():
            link.unlink()
        os.symlink(os.path.relpath(target, probe_dir), link, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        return False
    finally:
        for p in (link, target):
            try:
                if p.is_symlink():
                    p.unlink()
                elif p.is_dir():
                    p.rmdir()
            except OSError:
                pass


def iter_files(root: Path) -> Iterable[Path]:
    if root.exists():
        yield from sorted(p for p in root.rglob("*") if p.is_file())
