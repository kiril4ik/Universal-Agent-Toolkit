"""MCP configuration.

One neutral server spec per MCP pack; per-agent shapes are derived here.
Existing config files are merged key-by-key and never rewritten wholesale,
because they usually contain servers we know nothing about.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .registry import Agent
from .util import CONFLICT, SAME, ADD, OVERWRITE, Report, ToolkitError, dumps_json


@dataclass
class ServerSpec:
    name: str
    title: str
    summary: str
    command: str
    args: list[str]
    env: dict[str, str]
    required_env: list[str]
    required_apps: list[str]
    risk: str
    setup: str
    url: str = ""
    transport: str = "stdio"
    scope: str = "project"

    @classmethod
    def from_json(cls, path: Path) -> "ServerSpec":
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ToolkitError(f"invalid MCP spec {path}: {exc}") from exc
        if "name" not in d:
            raise ToolkitError(f"MCP spec {path} missing key: name")
        if not d.get("command") and not d.get("url"):
            raise ToolkitError(
                f"MCP spec {path} needs either 'command' (stdio) or 'url' (http/sse)"
            )
        req = d.get("requires") or {}
        scope = d.get("scope", "project")
        if scope not in ("project", "user"):
            raise ToolkitError(
                f"MCP spec {path}: scope must be 'project' or 'user', got {scope!r}"
            )
        return cls(
            name=d["name"],
            title=d.get("title", d["name"]),
            summary=d.get("summary", ""),
            command=d.get("command", ""),
            args=list(d.get("args") or []),
            env=dict(d.get("env") or {}),
            url=d.get("url", ""),
            transport=d.get("transport", "http" if d.get("url") else "stdio"),
            required_env=list(req.get("env") or []),
            required_apps=list(req.get("apps") or []),
            risk=d.get("risk", "low"),
            setup=d.get("setup", ""),
            scope=scope,
        )

    @property
    def needs_manual_setup(self) -> bool:
        return bool(self.required_env or self.required_apps)


def shape_entry(spec: ServerSpec, shape: str) -> dict[str, Any]:
    """Convert a neutral spec into one tool's expected entry shape."""
    if spec.url:
        # Remote / local-HTTP servers (e.g. Figma's Dev Mode server).
        if shape == "opencode":
            return {"type": "remote", "url": spec.url, "enabled": True}
        if shape == "zed":
            return {"source": "custom", "url": spec.url}
        return {"type": spec.transport, "url": spec.url}

    if shape == "opencode":
        entry: dict[str, Any] = {
            "type": "local",
            "command": [spec.command, *spec.args],
            "enabled": True,
        }
        if spec.env:
            entry["environment"] = spec.env
        return entry

    if shape == "zed":
        entry = {"command": spec.command, "args": spec.args}
        if spec.env:
            entry["env"] = spec.env
        return {"source": "custom", **entry}

    # "standard" (Claude Code, Cursor, Gemini, Roo, Kilo) and VS Code.
    entry = {"command": spec.command, "args": spec.args}
    if spec.env:
        entry["env"] = spec.env
    if shape == "vscode":
        entry = {"type": "stdio", **entry}
    return entry


def write_agent_mcp(
    agent: Agent,
    project: Path,
    specs: list[ServerSpec],
    *,
    force: bool,
    report: Report,
) -> None:
    """Merge our servers into this agent's project-scoped MCP config."""
    if not agent.writes_project_mcp or not specs:
        return

    # A user-scoped server belongs to an individual account, not to the
    # repository. Writing it into a committed config would hand every
    # teammate an entry that cannot work until they personally sign in -
    # and the toolkit never writes outside the project, so the only honest
    # option is to document it. manual_setup_notes() does that.
    specs = [s for s in specs if s.scope != "user"]
    if not specs:
        return

    cfg = agent.mcp
    path = project / cfg["path"]
    key = cfg.get("key") or "mcpServers"
    shape = cfg.get("shape", "standard")

    if path.exists():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report.record(CONFLICT, path, "existing file is not valid JSON; left untouched")
            return
        if not isinstance(doc, dict):
            report.record(CONFLICT, path, "existing config is not a JSON object; left untouched")
            return
    else:
        doc = {}

    bucket = doc.get(key)
    if bucket is None:
        bucket = {}
        doc[key] = bucket
    elif not isinstance(bucket, dict):
        report.record(CONFLICT, path, f"existing '{key}' is not an object; left untouched")
        return

    changed = False
    for spec in specs:
        entry = shape_entry(spec, shape)
        if spec.name in bucket:
            if bucket[spec.name] == entry:
                report.record(SAME, path, f"server '{spec.name}'")
                continue
            if not force:
                report.record(CONFLICT, path, f"server '{spec.name}' differs; kept existing")
                continue
            report.record(OVERWRITE, path, f"server '{spec.name}'")
        else:
            report.record(ADD, path, f"server '{spec.name}'")
        bucket[spec.name] = entry
        changed = True

    if changed and not report.dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dumps_json(doc), encoding="utf-8")


def manual_setup_notes(agents: list[Agent], specs: list[ServerSpec]) -> str:
    """Markdown describing whatever the installer could not do automatically."""
    lines = [
        "# MCP servers",
        "",
        "Configured by the Universal Agent Toolkit. Neutral specs live in",
        "`.agent-toolkit/mcp/*.json`; each tool's own config was generated from them.",
        "",
    ]

    lines += ["## Installed servers", ""]
    for spec in sorted(specs, key=lambda s: s.name):
        risk = {"low": "", "medium": " _(medium risk)_", "high": " **(high risk)**"}.get(spec.risk, "")
        lines.append(f"### `{spec.name}` - {spec.title}{risk}")
        if spec.summary:
            lines.append("")
            lines.append(spec.summary)
        lines.append("")
        if spec.url:
            lines.append(f"Endpoint: `{spec.url}` ({spec.transport})")
        else:
            lines.append(f"Command: `{spec.command} {' '.join(spec.args)}`")
        lines.append("")
        if spec.scope == "user":
            lines.append(
                "**Account-scoped: not written into this project's config.** "
                "It belongs to your own account, so a committed entry would not "
                "work for teammates. Add it yourself with the command below - "
                "once per machine, not once per project."
            )
            lines.append("")
        if spec.required_env:
            lines.append("Required environment variables (set these yourself):")
            lines.append("")
            for var in spec.required_env:
                lines.append(f"- `{var}`")
            lines.append("")
        if spec.required_apps:
            lines.append("Requires these to be installed and running:")
            lines.append("")
            for app in spec.required_apps:
                lines.append(f"- {app}")
            lines.append("")
        if spec.setup:
            lines.append(spec.setup.strip())
            lines.append("")

    globals_needed = [a for a in agents if a.mcp_scope == "global"]
    if globals_needed:
        lines += [
            "## Manual configuration required",
            "",
            "These tools keep MCP configuration outside the project, so the installer",
            "cannot write it. Add the servers above by hand:",
            "",
        ]
        for a in globals_needed:
            lines.append(f"- **{a.name}** - `{a.mcp.get('path')}`")
        lines.append("")

    unsupported = [a for a in agents if a.mcp_scope == "unsupported"]
    if unsupported:
        lines += [
            "## No MCP support",
            "",
            *[f"- {a.name}" for a in unsupported],
            "",
        ]

    return "\n".join(lines).rstrip() + "\n"
