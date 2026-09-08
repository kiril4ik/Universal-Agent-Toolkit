# Agent support

Fourteen coding agents. Selecting one **never** creates another's files — no
`.cursor/` in a Claude Code project, no `GEMINI.md` in a Codex project.

Check what your tool gets before installing:

```bash
uat agents
uat agents --show cursor
```

## The matrix

| Agent | `--agent` id | Instruction file | Skills mount | MCP config | Confidence |
|---|---|---|---|---|---|
| Claude Code | `claude-code` | `CLAUDE.md` | `.claude/skills` | `.mcp.json` (project) | high |
| Cursor | `cursor` | `.cursor/rules/00-agent-toolkit.mdc` | — | `.cursor/mcp.json` (project) | high |
| OpenAI Codex CLI | `codex` | `AGENTS.md` | `.agents/skills` | `~/.codex/config.toml` (global) | high |
| GitHub Copilot / VS Code | `copilot` | `.github/copilot-instructions.md` | — | `.vscode/mcp.json` (project) | high |
| Gemini CLI | `gemini-cli` | `GEMINI.md` | — | `.gemini/settings.json` (project) | high |
| Windsurf | `windsurf` | `.windsurf/rules/00-agent-toolkit.md` | — | `~/.codeium/windsurf/mcp_config.json` (global) | medium |
| Cline | `cline` | `.clinerules/00-agent-toolkit.md` | — | `cline_mcp_settings.json` (global) | high |
| Roo Code | `roo` | `.roo/rules/00-agent-toolkit.md` | — | `.roo/mcp.json` (project) | high |
| JetBrains Junie | `junie` | `AGENTS.md` | — | IDE settings (global) | high |
| OpenCode | `opencode` | `AGENTS.md` | — | `opencode.json` (project) | high |
| Aider | `aider` | `CONVENTIONS.md` | — | not supported | high |
| Amp | `amp` | `AGENTS.md` | — | Amp settings (global) | high |
| Zed | `zed` | `.rules` | — | `~/.config/zed/settings.json` (global) | high |
| Kilo Code | `kilocode` | `.kilocode/rules/00-agent-toolkit.md` | — | `.kilocode/mcp.json` (project) | medium |

Aliases work too: `--agent claude` and `--agent claude-cli` both resolve to
`claude-code`.

### What "confidence" means

How well the format has been verified against the vendor's own published
documentation, not how good the tool is.

- **high** — the paths and config keys were checked against official docs.
- **medium** — the format is documented less precisely, or has changed
  recently. Confirm with `uat agents --show <id>` and your tool's docs before
  relying on the MCP surface.

An agent spec being wrong is a data bug. It is fixed in
[`catalog/agents.json`](../catalog/agents.json) — never in code.

### Global vs project MCP scope

Where the column says **global**, the tool has no project-scoped MCP
configuration. The toolkit does not write to your home directory during an
install. Instead it writes a neutral server spec to
`.agent-toolkit/mcp/<server>.json` and records in `.agent-toolkit/mcp/README.md`
what you need to paste where. Project-scoped tools get their config written
directly, merged into any existing file rather than replacing it.

## What every agent receives

Regardless of tool:

- `.agent-toolkit/` — the whole content tree: core policy, workflow, rules,
  skills, reports.
- An **instruction file that is a pointer, not a copy.** It is ~600 bytes and
  routes to `.agent-toolkit/CORE.md`. Rule bodies are never inlined into a
  file the agent auto-loads every session — that would be context bloat in
  every project, forever.

```markdown
# AI agent instructions

This project is configured by the Universal Agent Toolkit.

**Start here: `.agent-toolkit/CORE.md`**

That file routes you to the safety rules, the stack rules that apply to
what you are touching, the planning workflow, and the available skills.
It is deliberately short - read it fully.
```

## What only some agents receive

### Native skill discovery — Claude Code and Codex

Both have a real skills directory, so both get one mounted:

```
.claude/skills  -> ../.agent-toolkit/skills     (Claude Code)
.agents/skills  -> ../.agent-toolkit/skills     (Codex)
```

It is a **symlink**, so nothing is duplicated on disk. Use `--copy` on
filesystems without symlink support.

Every other agent gets exactly the same content — it is all plain Markdown
under `.agent-toolkit/skills/` — but has to be pointed at it rather than
discovering it. `CORE.md` lists the skill files for precisely this reason.

### Slash commands and subagents — Claude Code

```
.claude/commands/plan.md          /plan <what you want to build>
.claude/commands/plan-status.md   /plan-status
.claude/commands/plan-resume.md   /plan-resume
```

`.claude/agents/` is declared as a surface for subagent definitions and shows
up in the install plan, but no pack currently ships any, so the directory
stays empty.

Every other agent gets the same trigger as a copy-paste prompt in
`.agent-toolkit/START-HERE.md`.

### Session hooks — Claude Code

The `session-reminder` pack registers a `SessionStart` hook in
`.claude/settings.json` that injects the non-negotiables into context at the
start of *every* session. This is the difference between rules being
*available* and rules being *used*.

```bash
uat install --project . --agent claude-code --add session-reminder
```

Your tool will ask you to approve the hook the first time. That prompt is
expected. See [Troubleshooting](TROUBLESHOOTING.md#the-agent-ignores-the-rules).

## Configuring several agents

```bash
uat install --project ~/app --agent claude-code --agent cursor
uat install --project ~/app --agent all
```

Each agent's surfaces are written independently against the same
`.agent-toolkit/` content. There is one source of truth and several thin
pointers into it, so the tools cannot drift apart.

Re-installing **extends**: adding `--agent cursor` later keeps the Claude
Code configuration. `--replace` is how you deliberately drop one.

## Adding an agent

Tool-specific knowledge is data, so this is a JSON edit:

1. Add an entry to [`catalog/agents.json`](../catalog/agents.json):

```jsonc
{
  "id": "my-agent",
  "name": "My Agent",
  "aliases": ["mine"],
  "confidence": "medium",
  "surfaces": {
    "instructions": { "style": "root-pointer", "path": "AGENTS.md" },
    "mcp": { "scope": "project", "path": ".myagent/mcp.json",
             "key": "mcpServers", "shape": "standard" }
  },
  "notes": "Where the format was verified from."
}
```

2. `./bin/uat doctor` — the registry must still load.
3. `./bin/uat install --project /tmp/probe --agent my-agent --yes --dry-run` —
   confirm it writes what you expect and nothing else.
4. `./bin/uat-test`.

Available instruction styles: `root-pointer` (one file at a known path) and
`dir-rules-md` / `dir-rules-mdc` (a numbered file inside a rules directory).

**Set `confidence` honestly.** A guessed path that silently writes to the
wrong place is worse than an unsupported tool, because the user believes it
worked. If you have not read the vendor's documentation, it is not `high`.

## Related

- [CLI reference](CLI.md#uat-agents)
- [Architecture](ARCHITECTURE.md#why-adapters-are-pointers) — why the
  instruction files are pointers
- [Troubleshooting](TROUBLESHOOTING.md)
