# Architecture

## Two stages

**Stage A — the library (this repository).** Pinned upstream material,
verified by content hash, plus our own policy and the planning workflow. Broad
on purpose: it holds rules for technologies most projects will never use.

**Stage B — the install (a target project).** Detect the stack, select packs,
and write only what the selected agents read. Narrow on purpose.

The installer is the boundary between them. Breadth costs nothing here;
it costs context there.

## Layers

### `vendor/`
Verbatim upstream snapshots. Each carries `SOURCE.json` with the repository,
the pinned commit, the licence, the included paths and a `content_sha256`.
`uat vendor verify` recomputes that hash, so an edited snapshot is a hard
failure rather than a silent divergence from what the provenance claims.

### `catalog/core/`
Policy we author and own: safety, git hygiene, verification, interaction
modes. Always installed, because it applies regardless of stack.

### `catalog/workflow/`
The twelve-phase planning sequence, written to be executable by any agent —
plain Markdown, no tool-specific features.

### `catalog/packs/<id>/`
The unit of installation. A pack contributes files under `files/` and/or maps
part of a vendored snapshot via `vendor_maps`. Everything a pack provides
lands under the project's `.agent-toolkit/`.

Two vendor-map forms:

```jsonc
// directory: copy a whole skill in
{ "vendor": "superpowers", "src": "skills", "dest": "skills" }

// file: a vendored name becomes a clean rule name
{ "vendor": "awesome-copilot",
  "files": [{ "from": "instructions/go.instructions.md", "to": "rules/GO.md" }] }
```

### `catalog/agents.json`
The only place tool-specific paths and config keys exist. Each agent declares
its instruction surface, whether it supports skills, and how its MCP config is
shaped and scoped. Adding an agent is a data edit.

Instruction styles: `root-pointer` (a file at the project root),
`dir-rules-md`, `dir-rules-mdc` (Cursor's YAML frontmatter form).

MCP scopes: `project` (we write it), `global` (the tool stores it outside the
project — we emit manual instructions instead), `unsupported`.

## Why adapters are pointers

Generated tool files are ~600 bytes and route to `.agent-toolkit/CORE.md`,
which is itself a router listing what exists and when to read it.

The alternative — inlining rules into `CLAUDE.md` / `AGENTS.md` — puts every
rule in context on every turn of every task, including the ones irrelevant to
what is being changed. Two tests enforce this: `CORE.md` must stay under 6 KB,
and it must not contain the body of any rule file.

## Why skills are symlinked

Claude Code requires skills in `.claude/skills/`. Copying them there would
mean two copies of several megabytes, drifting apart. The installer symlinks
`.claude/skills -> ../.agent-toolkit/skills`, and falls back to copying when
the filesystem refuses — detected empirically, not guessed from the platform.

## Idempotency and state

`.agent-toolkit/installed.json` records a content hash for every file the
installer wrote. Re-running is safe: identical files are skipped, divergent
ones are reported as conflicts and kept.

The hash recorded is of **what the toolkit installed**, not of what is on disk
afterwards. A file we refused to overwrite keeps its previous recorded hash —
otherwise a user's edit would silently become the new baseline and
`uat status` would report no drift.

## Trust boundary

Vendored skills are executable instructions, so they are treated like code
dependencies: pinned to a commit, hashed, reviewed on update, and never
fetched during ordinary project work.
