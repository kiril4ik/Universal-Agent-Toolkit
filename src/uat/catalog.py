"""Pack catalog.

A pack is the unit of installation. Everything a pack provides lands
under the project's single `.agent-toolkit/` directory - never scattered
across the project root.

Content comes from one or both of:
  * catalog/packs/<id>/files/**   - content we author and own
  * vendor/<vendor-id>/**         - verbatim upstream snapshots (see vendorlib)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .util import ToolkitError, read_json

TIERS = ("core", "recommended", "optional")


@dataclass
class VendorMap:
    """Maps part of a vendored snapshot into .agent-toolkit/.

    Two forms, which may be combined:
      * directory form - copy `src` (a directory) to `dest`, honouring
        `only` / `exclude`
      * file form      - copy each (from, to) pair in `files`, which lets a
        vendored `go.instructions.md` land as a clean `rules/GO.md`
    """

    vendor: str
    src: str = ""
    dest: str = ""
    only: tuple[str, ...] = ()          # if set, only these child dirs/files
    exclude: tuple[str, ...] = ()
    files: tuple[tuple[str, str], ...] = ()

    def required_paths(self) -> list[str]:
        """Paths inside the vendor snapshot this map depends on."""
        if self.files:
            return [src for src, _ in self.files]
        return [self.src] if self.src else []


@dataclass
class Pack:
    id: str
    title: str
    tier: str
    summary: str
    tags: tuple[str, ...] = ()
    detect: tuple[str, ...] = ()        # stack tokens that recommend this pack
    requires: tuple[str, ...] = ()
    vendor_maps: tuple[VendorMap, ...] = ()
    root: Path = field(default=Path("."))

    @property
    def files_dir(self) -> Path:
        return self.root / "files"

    @property
    def is_mcp(self) -> bool:
        return "mcp" in self.tags or self.id.startswith("mcp-")

    def provides(self) -> dict[str, int]:
        """Rough content census, for `uat catalog list`."""
        out = {"rules": 0, "skills": 0, "mcp": 0, "workflow": 0, "other": 0}
        for p in self.files_dir.rglob("*") if self.files_dir.exists() else []:
            if not p.is_file():
                continue
            top = p.relative_to(self.files_dir).parts[0]
            if top == "skills":
                # count skill directories, not files
                continue
            out[top if top in out else "other"] += 1
        skills_dir = self.files_dir / "skills"
        if skills_dir.exists():
            out["skills"] = len([d for d in skills_dir.iterdir() if d.is_dir()])
        for vm in self.vendor_maps:
            if vm.files:
                for _, to in vm.files:
                    top = to.split("/", 1)[0]
                    out[top if top in out else "other"] += 1
            else:
                top = vm.dest.split("/", 1)[0]
                count = len(vm.only) if vm.only else 1
                out[top if top in out else "other"] += count
        return out


class Catalog:
    def __init__(self, packs: list[Pack], profiles: dict[str, Any]):
        self._packs = {p.id: p for p in packs}
        self.profiles = profiles

    @classmethod
    def load(cls, root: Path) -> "Catalog":
        packs_dir = root / "catalog" / "packs"
        if not packs_dir.exists():
            raise ToolkitError(f"catalog directory not found: {packs_dir}")

        packs: list[Pack] = []
        for pack_json in sorted(packs_dir.glob("*/pack.json")):
            data = read_json(pack_json)
            pid = data.get("id") or pack_json.parent.name
            if pid != pack_json.parent.name:
                raise ToolkitError(
                    f"pack id {pid!r} does not match directory {pack_json.parent.name!r}"
                )
            tier = data.get("tier", "optional")
            if tier not in TIERS:
                raise ToolkitError(f"pack {pid}: tier must be one of {TIERS}, got {tier!r}")
            vms = []
            for vm in data.get("vendor_maps", []):
                files = tuple(
                    (f["from"], f["to"]) for f in (vm.get("files") or [])
                )
                if not files and not vm.get("dest"):
                    raise ToolkitError(
                        f"pack {pid}: vendor_map needs either 'files' or 'src'+'dest'"
                    )
                vms.append(
                    VendorMap(
                        vendor=vm["vendor"],
                        src=vm.get("src", ""),
                        dest=vm.get("dest", ""),
                        only=tuple(vm.get("only") or ()),
                        exclude=tuple(vm.get("exclude") or ()),
                        files=files,
                    )
                )
            vms = tuple(vms)
            packs.append(
                Pack(
                    id=pid,
                    title=data.get("title", pid),
                    tier=tier,
                    summary=data.get("summary", ""),
                    tags=tuple(data.get("tags") or ()),
                    detect=tuple(data.get("detect") or ()),
                    requires=tuple(data.get("requires") or ()),
                    vendor_maps=vms,
                    root=pack_json.parent,
                )
            )

        profiles: dict[str, Any] = {}
        prof_dir = root / "catalog" / "profiles"
        if prof_dir.exists():
            for pf in sorted(prof_dir.glob("*.json")):
                profiles[pf.stem] = read_json(pf)

        catalog = cls(packs, profiles)
        catalog.validate()
        return catalog

    def validate(self) -> None:
        for pack in self._packs.values():
            for dep in pack.requires:
                if dep not in self._packs:
                    raise ToolkitError(f"pack {pack.id} requires unknown pack {dep!r}")
        for name, prof in self.profiles.items():
            for pid in prof.get("packs", []):
                if pid not in self._packs:
                    raise ToolkitError(f"profile {name} references unknown pack {pid!r}")

    # ------------------------------------------------------------------
    def __iter__(self):
        return iter(sorted(self._packs.values(), key=lambda p: (TIERS.index(p.tier), p.id)))

    def __contains__(self, pid: str) -> bool:
        return pid in self._packs

    def __len__(self) -> int:
        return len(self._packs)

    def get(self, pid: str) -> Pack:
        if pid not in self._packs:
            raise ToolkitError(
                f"unknown pack {pid!r}. Run `uat catalog list` to see available packs."
            )
        return self._packs[pid]

    @property
    def ids(self) -> list[str]:
        return sorted(self._packs)

    def by_tier(self, tier: str) -> list[Pack]:
        return [p for p in self if p.tier == tier]

    def expand(self, ids: set[str]) -> set[str]:
        """Close the selection over `requires`."""
        out = set()
        stack = list(ids)
        while stack:
            pid = stack.pop()
            if pid in out:
                continue
            pack = self.get(pid)
            out.add(pid)
            stack.extend(d for d in pack.requires if d not in out)
        return out

    def recommend(self, stack_tokens: set[str], *, include_optional: bool = False) -> set[str]:
        """Core packs always; others when the detected stack asks for them."""
        chosen: set[str] = set()
        for pack in self:
            if pack.tier == "core":
                chosen.add(pack.id)
            elif pack.detect and (set(pack.detect) & stack_tokens):
                chosen.add(pack.id)
            elif include_optional and pack.tier == "recommended":
                chosen.add(pack.id)
        return self.expand(chosen)

    def resolve_profile(self, name: str) -> set[str]:
        if name not in self.profiles:
            raise ToolkitError(
                f"unknown profile {name!r}. Available: {', '.join(sorted(self.profiles)) or 'none'}"
            )
        prof = self.profiles[name]
        ids = set(prof.get("packs", []))
        for parent in prof.get("extends", []):
            ids |= self.resolve_profile(parent)
        return self.expand(ids)


# ----------------------------------------------------------------------
# reachability
# ----------------------------------------------------------------------

# Directories inside a snapshot whose children are individually installable.
_SKILL_ROOTS = {
    "superpowers": "skills",
    "vercel-agent-skills": "skills",
    "ui-ux-pro-max": ".claude/skills",
}


def unreachable_vendor_content(catalog: "Catalog", toolkit_root: Path) -> dict[str, list[str]]:
    """Vendored skill directories that no pack can install.

    Vendoring something no pack maps is dead weight: it costs repository size
    and implies a capability that cannot actually be installed.
    """
    mapped: set[tuple[str, str]] = set()
    for pack in catalog:
        for vm in pack.vendor_maps:
            if vm.src:
                mapped.add((vm.vendor, vm.src))
            for src, _ in vm.files:
                mapped.add((vm.vendor, src))

    out: dict[str, list[str]] = {}
    for vendor, root in _SKILL_ROOTS.items():
        base = toolkit_root / "vendor" / vendor / root
        if not base.is_dir():
            continue
        if (vendor, root) in mapped:      # whole directory is mapped
            continue
        orphans = [
            d.name for d in sorted(base.iterdir())
            if d.is_dir() and (vendor, f"{root}/{d.name}") not in mapped
        ]
        if orphans:
            out[vendor] = orphans
    return out


def unmapped_rule_files(catalog: "Catalog", toolkit_root: Path) -> dict[str, int]:
    """Count vendored rule documents that no pack exposes.

    Unlike orphaned skills this is expected: the rule libraries are broad on
    purpose and packs are added on demand. Reported so the ratio is visible.
    """
    used: set[tuple[str, str]] = set()
    for pack in catalog:
        for vm in pack.vendor_maps:
            for src, _ in vm.files:
                used.add((vm.vendor, src))

    out: dict[str, int] = {}
    for vendor, sub, ext in (
        ("awesome-copilot", "instructions", ".instructions.md"),
        ("awesome-cursorrules", "rules", ".mdc"),
    ):
        base = toolkit_root / "vendor" / vendor / sub
        if not base.is_dir():
            continue
        total = list(base.glob("*" + ext))
        out[vendor] = len([f for f in total
                           if (vendor, f"{sub}/{f.name}") not in used])
    return out
