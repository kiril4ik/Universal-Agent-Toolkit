"""Agent registry: the single source of truth for tool-specific surfaces.

Nothing else in the codebase may hardcode a tool path or config key.
Adding support for a new coding agent means editing catalog/agents.json.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .util import ToolkitError, read_json


@dataclass(frozen=True)
class Agent:
    id: str
    name: str
    aliases: tuple[str, ...]
    confidence: str
    surfaces: dict[str, Any]
    notes: str

    # -- instructions -------------------------------------------------
    @property
    def instructions(self) -> dict[str, Any]:
        return self.surfaces.get("instructions") or {}

    @property
    def instruction_path(self) -> str | None:
        ins = self.instructions
        style = ins.get("style")
        if style == "root-pointer":
            return ins.get("path")
        if style in ("dir-rules-md", "dir-rules-mdc"):
            return f"{ins['path']}/{ins['filename']}"
        return None

    @property
    def extra_root_files(self) -> list[str]:
        return list(self.surfaces.get("also_writes") or [])

    # -- skills -------------------------------------------------------
    @property
    def skills_path(self) -> str | None:
        s = self.surfaces.get("skills") or {}
        return s.get("path")

    @property
    def supports_skills(self) -> bool:
        return bool(self.skills_path)

    # -- mcp ----------------------------------------------------------
    @property
    def mcp(self) -> dict[str, Any]:
        return self.surfaces.get("mcp") or {}

    @property
    def mcp_scope(self) -> str:
        return self.mcp.get("scope", "unsupported")

    @property
    def writes_project_mcp(self) -> bool:
        return self.mcp_scope == "project" and bool(self.mcp.get("path"))

    def owned_paths(self) -> list[str]:
        """Every path this agent could cause the installer to create."""
        out: list[str] = []
        if self.instruction_path:
            out.append(self.instruction_path)
        out.extend(self.extra_root_files)
        if self.skills_path:
            out.append(self.skills_path)
        for key in ("commands", "subagents"):
            surface = self.surfaces.get(key)
            if surface and surface.get("path"):
                out.append(surface["path"])
        if self.writes_project_mcp:
            out.append(self.mcp["path"])
        hooks = self.surfaces.get("hooks") or {}
        if hooks.get("scope") == "project" and hooks.get("path"):
            out.append(hooks["path"])
        config = self.surfaces.get("config") or {}
        if config.get("path"):
            out.append(config["path"])
        return out

    @property
    def supports_hooks(self) -> bool:
        h = self.surfaces.get("hooks") or {}
        return h.get("scope") == "project" and bool(h.get("path"))


class Registry:
    def __init__(self, agents: list[Agent]):
        self._agents = agents
        self._by_key: dict[str, Agent] = {}
        for a in agents:
            self._by_key[a.id] = a
            for alias in a.aliases:
                self._by_key[alias] = a

    @classmethod
    def load(cls, root: Path) -> "Registry":
        data = read_json(root / "catalog" / "agents.json")
        agents = [
            Agent(
                id=item["id"],
                name=item["name"],
                aliases=tuple(item.get("aliases") or ()),
                confidence=item.get("confidence", "low"),
                surfaces=item.get("surfaces") or {},
                notes=item.get("notes", ""),
            )
            for item in data.get("agents", [])
        ]
        if not agents:
            raise ToolkitError("catalog/agents.json defines no agents")
        return cls(agents)

    def __iter__(self):
        return iter(self._agents)

    def __len__(self) -> int:
        return len(self._agents)

    @property
    def ids(self) -> list[str]:
        return [a.id for a in self._agents]

    def get(self, key: str) -> Agent:
        agent = self._by_key.get(key.strip().lower())
        if agent is None:
            raise ToolkitError(
                f"unknown agent {key!r}. Known agents: {', '.join(self.ids)}"
            )
        return agent

    def resolve(self, keys: list[str]) -> list[Agent]:
        """Resolve names to agents, de-duplicated, order preserved."""
        seen: set[str] = set()
        out: list[Agent] = []
        for key in keys:
            agent = self.get(key)
            if agent.id not in seen:
                seen.add(agent.id)
                out.append(agent)
        return out
