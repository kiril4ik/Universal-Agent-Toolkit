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
    """A vendored source: a pinned git repo, or a local directory.

    Local sources exist because not everything worth vendoring lives in a
    public git repository - house style guides, a company's internal rules,
    or a skill you wrote yourself. They are snapshotted and content-hashed
    exactly like git sources, so `vendor verify` protects them equally; they
    simply have no commit to pin.
    """

    id: str
    license: str
    kind: str = "git"                 # "git" | "local"
    repo: str = ""                    # git only
    ref: str = ""                     # git only
    path: str = ""                    # local only: where it was copied from
    include: tuple[str, ...] = ()
    notes: str = ""

    @property
    def is_local(self) -> bool:
        return self.kind == "local"

    @property
    def short_ref(self) -> str:
        return "local" if self.is_local else self.ref[:7]

    @property
    def origin(self) -> str:
        return self.path or "(snapshot only)" if self.is_local else self.repo


def load_upstreams(toolkit_root: Path) -> list[Upstream]:
    data = read_json(toolkit_root / "catalog" / "vendor.json")
    out = []
    for item in data.get("upstreams", []):
        kind = item.get("type", "git")
        required = ("id", "license") if kind == "local" else ("id", "repo", "ref", "license")
        for key in required:
            if key not in item:
                raise ToolkitError(f"vendor.json entry missing '{key}': {item}")
        if kind not in ("git", "local"):
            raise ToolkitError(f"vendor.json entry {item['id']}: unknown type {kind!r}")
        out.append(
            Upstream(
                id=item["id"],
                license=item["license"],
                kind=kind,
                repo=item.get("repo", ""),
                ref=item.get("ref", ""),
                path=item.get("path", ""),
                include=tuple(item.get("include") or ()),
                notes=item.get("notes", ""),
            )
        )
    return out


def register(toolkit_root: Path, entry: dict) -> None:
    """Add or replace an entry in catalog/vendor.json, preserving the rest."""
    path = toolkit_root / "catalog" / "vendor.json"
    data = read_json(path)
    ups = data.setdefault("upstreams", [])
    for i, item in enumerate(ups):
        if item.get("id") == entry["id"]:
            ups[i] = entry
            break
    else:
        ups.append(entry)
    path.write_text(dumps_json(data), encoding="utf-8")


def add_local(
    toolkit_root: Path,
    source: Path,
    *,
    vendor_id: str,
    license: str,
    notes: str = "",
    include: tuple[str, ...] = (),
    force: bool = False,
) -> tuple[str, str]:
    """Vendor a local directory: snapshot it, hash it, register it."""
    source = source.expanduser().resolve()
    if not source.is_dir():
        raise ToolkitError(f"not a directory: {source}")
    if not vendor_id.replace("-", "").replace("_", "").isalnum():
        raise ToolkitError(f"vendor id must be alphanumeric/dash/underscore: {vendor_id!r}")

    dest = toolkit_root / "vendor" / vendor_id
    if dest.exists() and not force:
        raise ToolkitError(
            f"vendor/{vendor_id} already exists. Use --force to replace it."
        )

    with tempfile.TemporaryDirectory(prefix="uat-local-") as tmp:
        staged = Path(tmp) / "staged"
        staged.mkdir()
        names = include or tuple(
            p.name for p in source.iterdir() if p.name not in (".git", ".DS_Store")
        )
        for rel in names:
            s_path = source / rel
            if not s_path.exists():
                raise ToolkitError(f"include path {rel!r} not found in {source}")
            t = staged / rel
            t.parent.mkdir(parents=True, exist_ok=True)
            if s_path.is_dir():
                shutil.copytree(s_path, t, ignore=shutil.ignore_patterns(".git", ".DS_Store"))
            else:
                shutil.copy2(s_path, t)

        content_hash = sha256_tree(staged)
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staged, dest)

    (dest / SOURCE_FILE).write_text(
        dumps_json(
            {
                "id": vendor_id,
                "type": "local",
                "path": str(source),
                "license": license,
                "include": list(names),
                "content_sha256": content_hash,
                "fetched_at": _dt.datetime.now(_dt.timezone.utc)
                .replace(microsecond=0)
                .isoformat(),
                "notes": notes,
                "_policy": (
                    "Local snapshot. Committed to this repository and verified by "
                    "content hash. Edit the ORIGINAL and re-run `uat vendor sync`, "
                    "not this copy."
                ),
            }
        ),
        encoding="utf-8",
    )

    register(
        toolkit_root,
        {
            "id": vendor_id,
            "type": "local",
            "path": str(source),
            "license": license,
            "include": list(names),
            "notes": notes or f"Local content vendored from {source}",
        },
    )
    return vendor_id, f"{content_hash[:12]} ({len(names)} top-level item(s))"


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

    if up.is_local:
        src = Path(up.path).expanduser() if up.path else None
        if src and src.is_dir():
            _id, detail = add_local(
                toolkit_root, src, vendor_id=up.id, license=up.license,
                notes=up.notes, include=up.include, force=True,
            )
            return "synced", detail
        ok, detail = verify_one(up, toolkit_root)
        if ok:
            return "unchanged", "local snapshot (source not on this machine)"
        return "drifted", detail
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
    if up.is_local:
        recorded = meta.get("content_sha256")
        if not recorded:
            return False, "snapshot has no content hash"
    elif meta.get("ref") != up.ref:
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
    return True, ("local snapshot verified" if up.is_local
                  else f"{up.short_ref} verified")


def vendored_ids(toolkit_root: Path) -> list[str]:
    vdir = toolkit_root / "vendor"
    if not vdir.exists():
        return []
    return sorted(p.name for p in vdir.iterdir() if p.is_dir() and not p.name.startswith("."))
