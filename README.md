# Universal Agent Toolkit

Install AI coding rules, skills, MCP servers and a project planning workflow
into any project — **for the coding agent you actually use, and nothing else.**

```bash
./bin/uat install --project ~/code/my-app --agent claude-code
```

That creates exactly one folder, `.agent-toolkit/`, plus the two or three
files Claude Code itself needs. It does not create `.cursor/`, `.windsurf/`,
`.clinerules`, `GEMINI.md` or anything else you did not ask for.

## Why

Every coding agent has its own instruction file, rules directory and MCP
configuration. Every project needs different rules. The usual result is a
project root littered with config for eight tools, none of which is current.

This repository separates two jobs:

1. **A broad library, maintained once** — pinned upstream rules, skills and
   MCP definitions, verified against their source commits.
2. **A narrow install, per project** — detect the stack, copy only what that
   project needs, generate only the surfaces that one agent reads.

## Quick start

```bash
./bin/uat agents                    # 14 supported agents and what each one gets
./bin/uat catalog                   # 45 packs and 6 profiles
./bin/uat detect  --project ~/app   # what stack is in there, and the evidence
./bin/uat install --project ~/app --agent claude-code
```

Add `--dry-run` to see every file that would change before anything does.

```bash
./bin/uat install --project ~/app --agent cursor --profile nextjs
./bin/uat install --project ~/app --agent claude-code --agent cursor
./bin/uat status    --project ~/app     # what is installed, and local drift
./bin/uat uninstall --project ~/app     # removes only what it created
```

Interactive by default: it asks for an interaction mode, then shows a
checklist of packs with the detected stack marked. `--yes` skips both.

## What a project gets

```
my-app/
├── .agent-toolkit/          <- everything lives here
│   ├── CORE.md              routing file: what exists, when to read it
│   ├── core/                safety, git, verification, interaction modes
│   ├── workflow/            the 12-phase planning workflow
│   ├── rules/               only the stack rules this project uses
│   ├── skills/              vendored skills, stored once
│   ├── mcp/                 neutral server specs + setup status
│   ├── deploy/  docker/     provisioning and local-dev templates
│   ├── reports/             one report per completed phase
│   ├── project.json         mode, agents, detected stack
│   └── installed.json       lockfile with content hashes
├── CLAUDE.md                <- a pointer, ~600 bytes
├── .claude/skills -> ../.agent-toolkit/skills
└── .mcp.json
```

Skills are **symlinked**, not copied, so nothing is duplicated on disk.
Use `--copy` on filesystems without symlink support.

## Supported agents

Claude Code, Cursor, Codex, GitHub Copilot / VS Code, Gemini CLI, Windsurf,
Cline, Roo Code, JetBrains Junie, OpenCode, Aider, Amp, Zed, Kilo Code.

Every tool-specific path and config key lives in
[`catalog/agents.json`](catalog/agents.json). A format change is a one-line
edit there, never a code change. Each agent carries a `confidence` rating for
how well its format is verified — check it with `uat agents --show cursor`.

Only Claude Code has native skills, so only Claude Code gets a skills mount.
Every other agent gets the same content as plain Markdown it can read.

## The planning workflow

`.agent-toolkit/workflow/` holds a twelve-phase sequence any agent can follow:

| | | |
|---|---|---|
| 00 triage | 01 discovery | 02 business logic |
| 03 screens & flows | 04 content | 05 design |
| 06 stack | 07 rules | 08 architecture |
| 09 environments | 10 implementation plan | 11 gate |

Triage picks the depth: a one-line fix runs discovery and stops; a new product
runs everything. **Phase 11 is never skipped** — nothing is implemented until
the artifacts are checked against each other and a human approves.

## Provenance is enforced, not claimed

Every vendored file is fetched from a pinned commit and hashed:

```bash
./bin/uat vendor list      # pins, licences and verification state
./bin/uat vendor verify    # re-hashes; a hand-edited snapshot fails loudly
./bin/uat vendor sync      # fetch at the pinned commits
```

| Upstream | Licence | What |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | MIT | 14 engineering-discipline skills |
| [github/awesome-copilot](https://github.com/github/awesome-copilot) | MIT | 193 technology instruction guides |
| [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) | CC0 | 257 community rules (gap filling) |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | MIT | React / Next.js best practices |
| [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) | MIT | Interface quality checklist |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | MIT | Design intelligence and palettes |
| [emavv/karpathy-guidelines](https://github.com/emavv/karpathy-guidelines) | MIT | Anti-overcomplication guardrails |

Vendored content is **never edited**. Our own policy lives in `catalog/core/`.

**Not vendored:** Figma's skills are governed by the Figma Developer Terms
rather than an open-source licence, so the `mcp-figma` pack ships our own
integration guide and tells you how to install theirs from source.

## Deployment

The `deploy-ubuntu` pack ships working, tested bash:

- `inspect-server.sh` — read-only audit; run it before touching any server
- `provision-clean.sh` — fresh Ubuntu to ready-to-host
- `provision-existing.sh` — adds an app to a server already running things:
  refuses a taken port, writes exactly one new nginx site, never modifies an
  existing config, validates before reloading, never touches a database
- `deploy.sh` — atomic symlink release with health check and auto-revert
- `rollback.sh` — return to a previous release

Verified by running them on Ubuntu 24.04, including `nginx -t` on the
generated config.

## Design rules

- **One folder.** Everything installed lives in `.agent-toolkit/`.
- **Only what is asked for.** Selecting one agent never creates another's files.
- **Pointers, not copies.** Tool files route to the canonical content.
- **No silent overwrite.** Existing files are kept and reported; `--force` is explicit.
- **Nothing global.** No global installs, ever.
- **Data is valuable.** Destructive operations are gated, including locally.
- **Evidence before claims.** See `catalog/core/VERIFICATION.md`.

## Requirements

Python 3.9+ and git. No dependencies, no install step, no build.

## Tests

```bash
./bin/uat-test     # 50 tests
./bin/uat doctor   # verify catalog, registry and vendored snapshots
```

## Adding things

- **A new agent** — add an entry to `catalog/agents.json`.
- **A new rule pack** — add `catalog/packs/<id>/pack.json`; map a vendored file
  or add your own under `files/`.
- **A new upstream** — add it to `catalog/vendor.json` and run `uat vendor sync`.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
