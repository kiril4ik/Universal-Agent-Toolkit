# Architecture

## Two-stage model

The toolkit deliberately separates **catalog maintenance** from **project execution**.

### Stage A — universal toolkit

Research and pin useful skills, rules, and MCP definitions once. Review third-party resources for safety, licensing, overlap, and freshness. Store provenance and snapshots locally.

### Stage B — project bootstrap

Inspect the target repository, detect its stack, present a selectable checklist, and copy only the relevant resources. Once installed, the target project is self-describing and does not depend on hidden global agent configuration.

## Layers

### `vendor/`
Pinned upstream material and provenance. Prefer immutable release tags or commit SHAs. Do not edit except to repair a serious problem; record any patch.

### `toolkit/core/`
Our always-on behavioral policy: project planning, data safety, Git hygiene, security, verification, Docker/deployment safety.

### `toolkit/packs/`
Installable units. A pack can contain skills, rules, MCP snippets, or adapter fragments. Packs are selected by profile, stack detection, or the interactive checklist.

### `.agent-toolkit/` in target projects
Generated local state: chosen interaction mode, installed-pack lock data, canonical local rules, MCP snippets, and reports.

### Tool bridges
`AGENTS.md` is the canonical instruction surface where supported. Tool-specific files are intentionally tiny bridges to reduce drift.

## Canonical skill location

Use `.agents/skills/` as the canonical cross-agent project skill directory. Mirror to `.claude/skills/` because Claude Code requires its own project skill location. Other native paths are generated only where they add real compatibility.

## Idempotency

Installer state is recorded in `.agent-toolkit/installed.json`. A second run must:

- detect identical installed files and skip them;
- preserve modified/existing files;
- show conflicts rather than overwrite;
- only overwrite with explicit `--force`;
- never use a destructive reset strategy.

## Trust boundary

Third-party skills are executable instructions. Treat them like code dependencies: pin them, inspect scripts/hooks, avoid mutable downloads during ordinary project work, and keep external actions/permissions narrow.
