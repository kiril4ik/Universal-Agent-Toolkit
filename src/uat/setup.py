"""Install a reusable toolkit copy for the current user."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .util import (
    ADD,
    CONFLICT,
    LINK,
    OVERWRITE,
    Report,
    SAME,
    ToolkitError,
    copy_file,
    copy_tree,
    write_text,
)
from .windows import add_to_user_path

APP_NAME = "Universal-Agent-Toolkit"
UNIX_BIN = ".local/bin"
PATH_BEGIN = "# >>> Universal Agent Toolkit PATH >>>"
PATH_END = "# <<< Universal Agent Toolkit PATH <<<"


@dataclass(frozen=True)
class SetupPaths:
    app_dir: Path
    bin_dir: Path
    launcher: Path
    profile: Path | None = None


@dataclass
class SetupResult:
    paths: SetupPaths
    report: Report
    notes: list[str] = field(default_factory=list)


def platform_paths(platform: str, home: Path, env: dict[str, str]) -> SetupPaths:
    """Return the per-user application and launcher paths for a platform."""
    if platform == "win32":
        local_app_data = env.get("LOCALAPPDATA")
        if not local_app_data:
            raise ToolkitError("LOCALAPPDATA is not set; cannot choose the Windows setup directory")
        app_dir = Path(local_app_data) / APP_NAME
        return SetupPaths(app_dir, app_dir / "bin", app_dir / "bin" / "uat.cmd")

    if platform == "darwin":
        app_dir = home / "Library" / "Application Support" / APP_NAME
    else:
        app_dir = home / ".local" / "share" / "universal-agent-toolkit"

    shell = Path(env.get("SHELL", "")).name
    profile = home / (".zprofile" if shell == "zsh" else ".profile")
    return SetupPaths(app_dir, app_dir / "bin", app_dir / "bin" / "uat", profile)


def _require_source(source: Path) -> None:
    required = (source / "src", source / "catalog", source / "vendor", source / "bin" / "uat")
    missing = [str(path.relative_to(source)) for path in required if not path.exists()]
    if missing:
        raise ToolkitError(
            "setup must run from a toolkit checkout; missing " + ", ".join(missing)
        )


def copy_runtime(
    source: Path,
    destination: Path,
    *,
    force: bool,
    report: Report,
) -> None:
    """Copy only the files needed by a standalone toolkit installation."""
    _require_source(source)

    for name in ("src", "catalog", "vendor"):
        copy_tree(source / name, destination / name, force=force, report=report)

    for name in ("VERSION", "LICENSE", "bin/uat", "bin/uat.cmd"):
        path = source / name
        if path.is_file():
            copy_file(path, destination / name, force=force, report=report)


def _profile_block() -> str:
    return (
        f"{PATH_BEGIN}\n"
        f"export PATH=\"$HOME/{UNIX_BIN}:$PATH\"\n"
        f"{PATH_END}\n"
    )


def _setup_unix_launcher(
    paths: SetupPaths,
    *,
    force: bool,
    report: Report,
) -> None:
    link = paths.profile.parent / UNIX_BIN / "uat"
    target = paths.launcher
    relative_target = os.path.relpath(target, link.parent)

    if link.exists() or link.is_symlink():
        if link.is_symlink() and Path(os.readlink(link)) == Path(relative_target):
            report.record(SAME, link, f"-> {relative_target}")
            return
        if not force:
            report.record(CONFLICT, link, "existing launcher kept; use --force to replace")
            return
        if not report.dry_run:
            link.unlink()
        report.record(OVERWRITE, link, f"-> {relative_target}")
    else:
        report.record(LINK, link, f"-> {relative_target}")

    if not report.dry_run:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(relative_target)


def _setup_unix_profile(profile: Path, *, report: Report) -> None:
    existing = profile.read_text(encoding="utf-8") if profile.exists() else ""
    if PATH_BEGIN in existing and PATH_END in existing:
        report.record(SAME, profile, "PATH block already present")
        return

    separator = "" if not existing or existing.endswith("\n") else "\n"
    content = existing + separator + _profile_block()
    write_text(profile, content, force=True, report=report)


def setup_toolkit(
    source: Path,
    *,
    platform: str | None = None,
    home: Path | None = None,
    env: dict[str, str] | None = None,
    force: bool = False,
    dry_run: bool = False,
    profile_override: Path | None = None,
) -> SetupResult:
    """Copy the toolkit and register its launcher for the current user."""
    source = source.resolve()
    home = Path.home() if home is None else home
    env = dict(os.environ) if env is None else env
    platform = sys.platform if platform is None else platform
    paths = platform_paths(platform, home, env)
    report = Report(dry_run=dry_run)

    copy_runtime(source, paths.app_dir, force=force, report=report)

    notes: list[str] = []
    if platform == "win32":
        if not dry_run:
            add_to_user_path(str(paths.bin_dir))
        notes.append("Restart your terminal application to use `uat`, or refresh its PATH.")
    else:
        profile = profile_override or paths.profile
        if profile is None:
            raise ToolkitError("could not choose a Unix shell profile")
        unix_paths = SetupPaths(paths.app_dir, paths.bin_dir, paths.launcher, profile)
        _setup_unix_launcher(unix_paths, force=force, report=report)
        _setup_unix_profile(profile, report=report)
        notes.append(f"Open a new shell to load PATH from {profile}.")
        notes.append(f"For this shell: export PATH=\"$HOME/{UNIX_BIN}:$PATH\"")

    return SetupResult(paths=paths, report=report, notes=notes)
