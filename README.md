# Universal Agent Toolkit

A repository-local, version-controlled foundation for **planning, building, reviewing, testing, and deploying software with AI coding agents**.

The idea is simple: prepare the good tools once, then every project receives only the skills, rules, and MCP integrations it actually needs.

## Why this exists

AI coding tools work much better when they share a disciplined workflow, reliable project context, and consistent safety rules. In practice, each tool has its own instruction files, skill directories, MCP configuration, and defaults. Projects also need different rules depending on their stack.

This repository separates two concerns:

1. **Universal toolkit maintenance** — research, audit, pin, and keep a reusable library of skills/rules/MCP definitions.
2. **Per-project bootstrap** — inspect a project, choose only relevant resources, and copy them locally without overwriting existing configuration.

It is intentionally **project-local**. A bootstrapped project should not depend on hidden global Claude/Codex/Cursor configuration.

## First command

```bash
./scripts/preinstall.sh --project /path/to/project
```

The installer first asks how autonomous the agent should be:

- **Thorough** — ask all questions that materially affect product, architecture, design, or implementation.
- **Focused** — ask only important/blocking questions; use sensible defaults for the rest. **Default.**
- **Autonomous** — make reasonable decisions independently; interrupt only for destructive/irreversible actions or truly ambiguous product decisions.

Then it detects the stack and shows an interactive checklist:

```text
Skills & Rules
  1 [x] Superpowers                     recommended
  2 [x] Karpathy Guidelines            core
  3 [x] Data & Docker Safety           core
  4 [x] Git / Atomic Commits           core
  5 [x] Security                       core
  6 [x] UI UX Pro Max                  frontend
  7 [x] Figma Design-to-Code           frontend
  8 [x] React Best Practices           detected: react
  9 [ ] Laravel Rules                  not detected

MCP
 10 [x] Playwright                     core
 11 [x] Context7                       core
 12 [x] Figma                          frontend
 13 [ ] GitHub                         optional
```

Toggle items by number, choose all with `a`, none with `n`, reset recommendations with `r`, then press Enter.

If a resource is already present, it is shown as `✓ installed — skip`. Re-running the installer is safe and idempotent. Existing project files are **never overwritten by default**.

## Core principles

- **Research once, reuse locally.** External resources are evaluated and pinned here before projects consume them.
- **Copy only what the project needs.** Backend-only projects do not receive Figma/UI packs. PHP projects do not receive Rust rules.
- **Load only what the current task needs.** A project may contain several skills without injecting all of them into every prompt.
- **No silent overwrite.** Existing instructions, skills, MCP configs, or project files are skipped unless `--force` is explicit.
- **Data is valuable by default.** Never assume a database/volume is disposable.
- **Atomic Git history.** Commit by coherent feature/change set. No AI attribution and no `Co-authored-by` trailers.
- **Evidence before completion.** Tests/build/lint/browser verification must actually run before claiming success.
- **No global install.** Project-local skills/config/runtime only.

## Repository layout

```text
.
├── AGENTS.md
├── CLAUDE.md
├── GEMINI.md
├── CONVENTIONS.md
├── toolkit/
│   ├── manifest.json
│   ├── core/
│   └── packs/
├── vendor/
├── profiles/
├── adapters/
├── templates/project/
├── scripts/
│   ├── preinstall.sh
│   ├── preinstall.py
│   ├── bootstrap-mcp-runtime.sh
│   └── verify-toolkit.sh
└── docs/
    ├── ARCHITECTURE.md
    ├── PROJECT-PLANNING.md
    ├── TOOL-COMPATIBILITY.md
    ├── MCP.md
    ├── DATA-SAFETY.md
    ├── ADDING-A-SKILL.md
    └── UPDATING-UPSTREAMS.md
```

## What a bootstrapped project gets

```text
project/
├── AGENTS.md
├── CLAUDE.md
├── GEMINI.md
├── CONVENTIONS.md
├── .agent-toolkit/
│   ├── CORE.md
│   ├── project.json
│   ├── installed.json
│   ├── rules/
│   ├── mcp/
│   └── reports/
├── .agents/skills/
├── .claude/skills/
├── .cursor/rules/
├── .windsurf/rules/
├── .github/copilot-instructions.md
├── .clinerules
├── .roo/rules/
└── .junie/guidelines.md
```

Only selected packs are copied.

## Recommended defaults

**Core:** Superpowers, Karpathy Guidelines, Git/atomic commits, data safety, security, verification, Playwright MCP, Context7 MCP.

**Frontend:** UI UX Pro Max, Figma skills/MCP, Web Interface Guidelines, Playwright visual verification.

**React/Next:** Vercel React best practices.

**Database:** database-specific rules plus mandatory data-safety rules.

## MCP philosophy

- **Core:** Playwright, Context7.
- **Design:** Figma remote MCP.
- **Optional authenticated:** GitHub, Sentry, project-specific services.
- **Dangerous/data-mutating:** database and infrastructure MCPs are never enabled with broad write permissions by default.

`bootstrap-mcp-runtime.sh` installs supported npm MCP runtimes under:

```text
<project>/.agent-toolkit/runtime/
```

Never globally. It checks installed versions first and skips exact matches.

Remote MCPs such as Figma do not have a local server package to install; this toolkit stores the endpoint configuration and local Figma skills.

## Project planning starts after bootstrap

```text
1. Run preinstall.sh
2. Choose interaction mode
3. Detect/choose local skills, rules, MCPs
4. Inspect the project
5. Ask questions according to the selected mode
6. Define business logic and pages
7. Generate realistic content
8. Prepare/generate design if applicable
9. Select technology stack
10. Add only missing relevant stack rules
11. Define architecture
12. Prepare Docker/local environment
13. Prepare clean-server + existing-server deployment
14. Create detailed implementation plan
15. Resolve final blockers/assumptions
16. Implement incrementally and verify each step
```

Every major phase should produce a short report under `.agent-toolkit/reports/`.

See [`docs/PROJECT-PLANNING.md`](docs/PROJECT-PLANNING.md).

## Data safety

Routine Docker rebuilds must preserve persistent volumes. Do not casually run:

```text
docker compose down -v
docker volume prune
docker system prune --volumes
php artisan migrate:fresh
php artisan db:wipe
DROP DATABASE
DROP SCHEMA
TRUNCATE <important table>
```

For significant production-like schema/data changes: identify the environment, make/verify a backup when risk warrants it, define recovery, then change data.

## Git policy

- Prefer Conventional Commit-style messages.
- One coherent feature/fix/refactor per commit.
- Do not mix unrelated cleanup into a feature commit.
- Commit only after relevant verification.
- Never add `Co-authored-by`, `Generated-by`, `AI-assisted`, model names, or similar AI attribution unless the human explicitly asks.

## Non-interactive usage

```bash
./scripts/preinstall.sh --project ../my-app --yes
./scripts/preinstall.sh --project ../my-app --all --yes
./scripts/preinstall.sh --project ../my-app --profile laravel-react --yes
./scripts/preinstall.sh --project ../my-app --dry-run
./scripts/preinstall.sh --project ../my-app --force
```

## Upstream provenance

Pinned upstream sources live in `vendor/SOURCES.md` and `toolkit/manifest.json`. Third-party snapshots stay as close to upstream as possible; our policy belongs in `toolkit/core/` and local packs.

The installer is the boundary: **broad library here, narrow project context there**.
