# Coding Tool Compatibility

The installer generates small bridge files so the same canonical policy is picked up by major coding agents.

| Tool | Project instructions | Project skills | MCP surface |
|---|---|---|---|
| Claude Code | `CLAUDE.md` → `AGENTS.md` | `.claude/skills/` | `.mcp.json` |
| OpenAI Codex | `AGENTS.md` | `.agents/skills/` | `.codex/config.toml` where supported |
| Cursor | `AGENTS.md`, `.cursor/rules/*.mdc` | `.agents/skills/` / `.cursor/skills/` | `.cursor/mcp.json` |
| GitHub Copilot / VS Code | `AGENTS.md`, `.github/copilot-instructions.md` | `.agents/skills/`, `.github/skills/` | `.vscode/mcp.json` |
| Gemini CLI | `GEMINI.md` | `.gemini/skills/` | `.gemini/settings.json` |
| Windsurf | `AGENTS.md`, `.windsurf/rules/` | tool/version dependent | adapter snippet |
| Cline | `.clinerules` | tool/version dependent | adapter snippet |
| Roo Code | `.roo/rules/` | tool/version dependent | adapter snippet |
| JetBrains Junie | `.junie/guidelines.md` | tool/version dependent | native/settings dependent |
| OpenCode | `AGENTS.md` | `.agents/skills/` | `opencode.json` |
| Aider | `CONVENTIONS.md` | n/a | n/a |

Do not duplicate long rules into every tool file. Bridges point agents to `.agent-toolkit/CORE.md` and selected local skill directories.

Tool formats evolve. Adapters are isolated so a format change does not rewrite canonical policy.
