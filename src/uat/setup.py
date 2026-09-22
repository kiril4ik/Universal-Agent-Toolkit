"""Install a reusable toolkit copy for the current user."""

from __future__ import annotations

import os
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

