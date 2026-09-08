"""Vendoring: fetch upstream material verbatim at a pinned commit.

The rule this module exists to enforce: if `vendor/<id>/SOURCE.json` claims
a commit, the bytes next to it were actually fetched from that commit. No
paraphrasing, no summarising, no "close enough". `uat vendor verify`
re-derives the content hash so a drifted or hand-edited snapshot is a
hard failure rather than a silent lie.
"""

from __future__ import annotations

import datetime as _dt
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .util import ToolkitError, dumps_json, read_json, sha256_tree

SOURCE_FILE = "SOURCE.json"


@dataclass
class Upstream:
    id: str
    repo: str
    ref: str
    license: str
    include: tuple[str, ...]
    notes: str = ""

    @property
    def short_ref(self) -> str:
        return self.ref[:7]


def load_upstreams(toolkit_root: Path) -> list[Upstream]:
    data = read_json(toolkit_root / "catalog" / "vendor.json")
    out = []
    for item in data.get("upstreams", []):
        for key in ("id", "repo", "ref", "license"):
            if key not in item:
                raise ToolkitError(f"vendor.json entry missing '{key}': {item}")
        out.append(
            Upstream(
                id=item["id"],
                repo=item["repo"],
                ref=item["ref"],
                license=item["license"],
                include=tuple(item.get("include") or ()),
                notes=item.get("notes", ""),
            )
        )
    return out


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, check=False, timeout=600
    )


def _fetch(up: Upstream, workdir: Path) -> Path:
    """Materialise the exact pinned commit into workdir/src."""
    src = workdir / "src"
    src.mkdir(parents=True, exist_ok=True)

    for cmd in (
        ["git", "init", "-q"],
        ["git", "remote", "add", "origin", up.repo],
    ):
        r = _run(cmd, cwd=src)
        if r.returncode != 0:
            raise ToolkitError(f"{up.id}: {' '.join(cmd)} failed: {r.stderr.strip()}")

    # Fast path: servers that allow fetching a bare SHA.
    r = _run(["git", "fetch", "--depth", "1", "origin", up.ref], cwd=src)
    if r.returncode != 0:
        # Fall back to a full history fetch, then check out the pin.
        r = _run(["git", "fetch", "--tags", "origin"], cwd=src)
        if r.returncode != 0:
            raise ToolkitError(
                f"{up.id}: cannot fetch {up.repo}: {r.stderr.strip() or 'network error'}"
            )

    r = _run(["git", "checkout", "-q", "--detach", up.ref], cwd=src)
    if r.returncode != 0:
        r2 = _run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], cwd=src)
        if r2.returncode != 0:
            raise ToolkitError(
                f"{up.id}: ref {up.ref} not found in {up.repo}: {r.stderr.strip()}"
            )
        head = _run(["git", "rev-parse", "HEAD"], cwd=src).stdout.strip()
        if head != up.ref:
            raise ToolkitError(
                f"{up.id}: pinned ref {up.ref} does not match fetched commit {head}. "
                "Update catalog/vendor.json deliberately."
            )
    return src


def sync_one(up: Upstream, toolkit_root: Path, *, force: bool = False) -> tuple[str, str]:
    """Fetch and store one upstream. Returns (status, detail)."""
    dest = toolkit_root / "vendor" / up.id
    existing = read_json(dest / SOURCE_FILE, default={})
    if existing.get("ref") == up.ref and not force:
        ok, detail = verify_one(up, toolkit_root)
        if ok:
            return "unchanged", f"already at {up.short_ref}"
        return "drifted", detail

    with tempfile.TemporaryDirectory(prefix="uat-vendor-") as tmp:
        workdir = Path(tmp)
        src = _fetch(up, workdir)

        staged = workdir / "staged"
        staged.mkdir()

        includes = up.include or tuple(
            p.name for p in src.iterdir() if p.name != ".git"
        )
        for rel in includes:
            s = src / rel
            if not s.exists():
                raise ToolkitError(
                    f"{up.id}: include path {rel!r} not present at {up.short_ref}"
                )
            t = staged / rel
            t.parent.mkdir(parents=True, exist_ok=True)
            if s.is_dir():
                shutil.copytree(s, t, ignore=shutil.ignore_patterns(".git"))
            else:
                shutil.copy2(s, t)

        content_hash = sha256_tree(staged)

        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staged, dest)

    (dest / SOURCE_FILE).write_text(
        dumps_json(
            {
                "id": up.id,
                "repo": up.repo,
                "ref": up.ref,
                "license": up.license,
                "include": list(up.include),
                "content_sha256": content_hash,
                "fetched_at": _dt.datetime.now(_dt.timezone.utc)
                .replace(microsecond=0)
                .isoformat(),
                "notes": up.notes,
                "_policy": (
                    "Verbatim upstream snapshot. Do not edit. "
                    "Toolkit policy belongs in catalog/core or catalog/packs."
                ),
            }
        ),
        encoding="utf-8",
    )
    return "synced", f"{up.short_ref} ({content_hash[:12]})"


def verify_one(up: Upstream, toolkit_root: Path) -> tuple[bool, str]:
    dest = toolkit_root / "vendor" / up.id
    if not dest.exists():
        return False, "not vendored - run `uat vendor sync`"
    meta = read_json(dest / SOURCE_FILE, default={})
    if not meta:
        return False, f"missing {SOURCE_FILE}"
    if meta.get("ref") != up.ref:
        return False, (
            f"pinned {up.short_ref} but snapshot is {str(meta.get('ref'))[:7]}"
        )
    recorded = meta.get("content_sha256")
    if not recorded:
        return False, "snapshot has no content hash"

    tmp = dest.parent / f".{up.id}-verify"
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(dest, tmp, ignore=shutil.ignore_patterns(SOURCE_FILE))
    try:
        actual = sha256_tree(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if actual != recorded:
        return False, "content modified since fetch (edited vendor snapshot?)"
    return True, f"{up.short_ref} verified"


def vendored_ids(toolkit_root: Path) -> list[str]:
    vdir = toolkit_root / "vendor"
    if not vdir.exists():
        return []
    return sorted(p.name for p in vdir.iterdir() if p.is_dir() and not p.name.startswith("."))
