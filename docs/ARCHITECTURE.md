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
The fourteen-phase planning sequence, written to be executable by any agent —
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

## Embedding

The toolkit repository is a factory: `bin/`, `src/`, `catalog/`, `vendor/`,
`tests/`, `docs/`. None of it belongs in a target project's root.

`uat install --embed` copies the parts a project could need — `src/`,
`catalog/`, a launcher, optionally `vendor/` — into
`<project>/.agent-toolkit/toolkit/`. Factory-only directories (`bin`, `tests`,
`docs`, `.git`) are never embedded.

This works because `cli.TOOLKIT_ROOT` is derived from `__file__`:
`src/uat/cli.py` -> `parents[2]`. In the embedded layout that resolves to
`.agent-toolkit/toolkit/`, so an embedded copy reads its own catalog and its
own vendor snapshots with no special casing. A test asserts that resolution.

Two depths:

- **slim** (default, ~900 KB) — CLI and catalog. Everything already installed
  works offline; installing a *new* pack needs `uat vendor sync` and network,
  because the upstream bytes are not present.
- **`--with-vendor`** (~10 MB) — every pinned snapshot too, so a new pack can
  be installed with no network at all.

`EMBEDDED.json` marks the copy and records which depth was used. `uat doctor`
reads it and reports missing vendor snapshots as an expected condition rather
than a failure, so a slim embed is healthy rather than broken.

## Triggering the workflow

A workflow nobody starts is documentation. Installing therefore generates the
entry point, not only the phase files:

- **Claude Code** — `.claude/commands/plan.md`, `plan-status.md`,
  `plan-resume.md`. Real slash commands, with frontmatter and `$ARGUMENTS`.
- **Every agent** — `.agent-toolkit/START-HERE.md`, which contains the same
  instruction as a prompt to paste, plus the phase table.
- **The shell** — `uat workflow --project .` reads `reports/` and prints which
  phases are done, which is next, and the prompt to continue with.

Progress is derived from the presence of `reports/NN-*.md`, so it survives
across sessions, agents and machines. There is no hidden state.

### Path portability

Generated files reference the CLI, and they get committed. Baking this
checkout's absolute path into them would break every other developer, so
`render.uat_invocation()` emits either `./.agent-toolkit/toolkit/uat` (when
the toolkit is embedded) or a plain `uat`, never an absolute path.
`START-HERE.md` explains which case applies. A test asserts that neither the
user's home directory nor the toolkit checkout path appears in any generated
file.

Because of this, `--embed` runs *before* the install renders anything: the
embedded launcher must exist for the generated commands to point at it.

## Composing with Superpowers instead of competing with it

Superpowers ships a complete engineering chain: `brainstorming` ->
`writing-plans` -> `subagent-driven-development` / `executing-plans` ->
`finishing-a-development-branch`. The first version of this workflow
paralleled it - its own classification vocabulary, its own plan format, its
own approval gate - which produced four live contradictions.

The resolution is a precedence rule, stated once in `workflow/README.md`:

> **Phases own the sequence and the gates. Skills own the technique inside a
> phase.**

From that, each conflict resolves deterministically:

| Conflict | Resolution |
|---|---|
| two classification vocabularies | classify once in phase 00; triage carries a mapping table to spike/bounded/architectural |
| one question per message vs batch | batch, because the workflow also runs on non-interactive agents; exception for thorough-mode design |
| two approval gates | brainstorming's gate *is* the gate for Task class; phase 11 is the gate otherwise |
| "only writing-plans may follow brainstorming" | that is its standalone path; here phases 03-09 sit between |

The division of labour: **Superpowers owns the engineering chain, this
workflow owns the product phases it has nothing for** - business logic,
screens and flows, content, design, stack selection, rules installation,
environments and deployment - plus the cross-artifact coherence gate.

Phase 10 therefore defines no plan format. It delegates to `writing-plans`
and uses that skill's own default location, `docs/superpowers/plans/`, so the
execution skills find the plan where they expect it. Both skills document that
user preference may override their paths, so no vendored file is edited.

A test asserts the precedence section covers every known conflict, and another
asserts no phase references a skill that is not actually vendored.

## Vendor reachability

Vendoring content no pack can install is dead weight: repository size for a
capability that cannot be reached. `uat doctor` fails when a vendored skill
directory has no pack mapping it, and `uat catalog --unmapped` lists vendored
rule documents with no pack - expected for the broad libraries, which are
mapped on demand.

## Making the rules unmissable

A rule an agent has to go looking for is a rule it will sometimes skip. The
toolkit therefore ships four layers of increasing force:

| Layer | Mechanism | Strength |
|---|---|---|
| passive | `CLAUDE.md` -> `CORE.md` -> workflow | agent must follow a pointer |
| active | `/plan` commands, `START-HERE.md` | user must invoke |
| enforced | `SessionStart` hook | injected every session |
| verifiable | `uat workflow` | human can check |

The hook is the one that changes outcomes, and it is the mechanism Superpowers
uses for exactly this reason. We vendor its `skills/` but not its `hooks/`, so
the `session-reminder` pack supplies our own: a short script that prints the
non-negotiables plus live workflow state, registered in the agent's settings.

Design constraints on that script:

- **Never blocks a session.** Every failure path exits 0 with no output; a
  directory that is not a configured project produces silence.
- **Reads live state.** Mode and phase progress come from `project.json` and
  `reports/`, so the banner reflects reality rather than install-time guesses.
- **Stays short.** It is prepended to every session; length is a recurring
  cost paid forever.
- **Merges, never replaces.** Settings files hold the user's own hooks and
  permissions. Install adds one entry; uninstall removes exactly that entry
  and deletes the file only if nothing else remains.

`surfaces.hooks` in the agent registry declares which agents support this.
Agents that do not simply skip the step - no `.claude/` directory appears for
a Cursor-only install.

## Curated packs versus the long tail

Two kinds of vendored content, with different reachability rules.

**Skills** are directories with behaviour. Each must have a pack: vendoring a
skill no pack installs is dead weight, so `uat doctor` fails on it.

**Rule documents** number 450 across the two libraries. About forty have
curated packs - the common stacks, carrying stack-detection tokens and a
reviewed one-line summary. The remainder are niche (single-vendor SDKs,
one cloud's tooling) or stack-combo files of variable quality.

Generating a pack per document would put 450 entries in `uat catalog` and
bury the curated forty, which are the ones worth recommending. So the long
tail is reached directly:

```bash
uat catalog --search <term>      # search all 450, marking which have packs
uat add-rule <vendor>:<name>     # install any one of them
```

This keeps two properties that would otherwise conflict: the catalog stays
short enough to read, and nothing vendored is unreachable. A pack is then an
*endorsement* - "this is good, and here is when it applies" - rather than the
only route to a file.

`add-rule` calls `install.refresh()`, which re-renders `CORE.md` and
`START-HERE.md` from what is actually on disk. The router is generated, so any
change to the installed rule set regenerates it rather than leaving a stale
list - including a human dropping a file into `rules/` by hand.

## One store, many pointers

`vendor/` and `catalog/packs/` are often mistaken for two copies of the same
material. They are not:

| | Holds | Size |
|---|---|---|
| `vendor/<id>/` | the actual bytes, from a pinned commit or a local snapshot | ~9.4 MB |
| `catalog/packs/<id>/pack.json` | which vendored file to install, as what, and when it applies | ~400 B each |

Content exists exactly once. A pack is a curated pointer plus metadata -
tier, tags, stack-detection tokens, a reviewed summary - so adding one costs
almost nothing and never duplicates a file.

Packs may also carry their own `files/` for content we author (the deploy
scripts, the session hook, the Figma integration guide). That content has no
upstream, so it lives with the pack rather than in `vendor/`.

## Local vendoring

Not every worthwhile source is a public git repository: house style guides,
a company's internal conventions, a skill you wrote. `uat vendor add-local`
snapshots a directory into `vendor/<id>/`, content-hashes it, and registers a
`{"type": "local"}` entry in `catalog/vendor.json`.

Local sources get the same integrity guarantee as git ones - `vendor verify`
recomputes the hash, so an edited snapshot fails - and differ only in what
`sync` does:

- source path present -> re-copy from it, refreshing the snapshot
- source path absent -> verify the committed snapshot and report `unchanged`

The second case is the normal one for a teammate who cloned the repository:
they have the snapshot, not your folder, and everything still works.

Copying a directory into `vendor/` by hand is *not* supported: it would be
ignored by sync, by verify, and by every pack. `uat doctor` fails on any
directory in `vendor/` that `catalog/vendor.json` does not declare.

A test also asserts no local entry records a path under `/tmp` or a home
directory, because `vendor.json` is committed and a path from one machine is
worse than useless on another.

## Ownership is recorded, not inferred

Uninstall used to decide whether a file was ours by looking for a
`.agent-toolkit` reference in its text. That deletes a hand-written `CLAUDE.md`
that merely *mentions* the toolkit - a file the installer had correctly
refused to overwrite minutes earlier.

`installed.json` now carries `agent_files`: every path written outside
`.agent-toolkit/`, with the hash we wrote. Uninstall consults it and reaches
one of three verdicts:

| Verdict | Condition | Action |
|---|---|---|
| ours | recorded, hash unchanged | remove |
| modified | recorded, hash differs | keep, and say why |
| theirs | not recorded | keep |

Installations predating this field fall back to the old heuristic, so an
upgrade can still clean up after itself.

## Completion is evidence, never proof

`uat workflow` used to mark a phase done when a file with the right name
existed. Twelve empty files therefore reported a finished project, including
the approval gate.

Reports are now classified by content: boilerplate, headings, empty table rows
and `TBD` markers are stripped, and what remains must be substantive. Phase 00
is exempt because triage deliberately writes no file - expecting one made the
session banner say "next phase: 00" forever, inviting the agent to re-run
triage every session.

Where a phase declares an artifact (`docs/architecture.md` and friends), its
presence is checked separately, so "report written, artifact missing" is
visible rather than counted as success.

Even a fully green run prints a caveat: the gate at phase 11 requires a human
approval that no file can record. The tool reports evidence of work; it cannot
certify that the work was accepted.

## Previews must not have side effects

The installer's dry run created the target directory (via the symlink probe)
and understated its own change list, because it derived the rule and skill
sets by scanning a directory the install had not populated yet.

Both are fixed by deriving from the catalogue instead of from disk:
`pack_outputs()` predicts what the selected packs produce, and the symlink
probe tests the project directory rather than creating `.agent-toolkit/`.

The deploy script had the mirror-image bug: its dry run `cd`-ed into a release
directory it had deliberately not created. Commands are now printed instead of
executed when the release path is absent.

## Acceptance is separate from verification

`core/VERIFICATION.md` governs a *change*: did this edit do what it claimed,
and did you run something that proves it. That is per-task, and it was the only
thing the workflow enforced.

Nothing consumed the user journeys. `docs/screens.md` fed phase 08 (design) and
phase 10 (plan) and then stopped, so a product could reach the end of phase 12
with a green suite while password reset, permission denial or payment retry had
never once been performed. The tests were written by the agent that wrote the
code, against the same understanding, and they cover tasks rather than
journeys - which is exactly the blind spot they cannot see.

Phase 13 closes the loop back to phase 03. Its checklist is not invented: every
journey in `docs/screens.md` must appear in the acceptance table, and a missing
row is a failed acceptance rather than an oversight.

Four rules make an exercise count, and they live in `VERIFICATION.md` because
they apply to ordinary changes too:

1. **Drive the flow, do not photograph it.** A screenshot proves a page
   rendered, nothing more.
2. **Observe through a different path than the one that caused it.** UI ->
   UI can pass on client-side state; reload, fresh session or a database query
   proves persistence.
3. **Test the denial, not only the permission.**
4. **Take the unhappy path at least once.** Expired token, declined card,
   duplicate submit - never the path anyone demos.

The report's most important column is the one that says NOT VERIFIED. A table
with gaps is honest; a table with no gaps because the gaps were omitted is the
failure this phase exists to prevent. The phase file says so explicitly, and
also states its own ceiling: it proves the journeys you defined were performed,
not that the product is correct.

## Absence of a record is not absence of the field

`installed.json` records `agent_files` - what the installer wrote outside
`.agent-toolkit/`. Uninstall originally treated an *empty* map as "this predates
provenance, fall back to guessing from file content".

But empty is a meaningful result: it means every candidate file already existed
and was preserved as a conflict, so the toolkit owns none of them. Install a
Codex configuration into a project that already has `AGENTS.md` and
`.agents/skills/` and that is exactly what you get - and the fallback then
deleted the user's `AGENTS.md` on the way back out.

Legacy is therefore detected by the *key's absence* (`"agent_files" not in
state`), never by its emptiness. Both cases are tested: an empty map must
preserve, a missing key must still clean up.

## One restart path, and rollback owns it

`deploy.sh` had two restart implementations: the deploy path honoured
`RESTART_CMD` and fell back to systemd, while the rollback path honoured
`RESTART_CMD` only. A systemd-managed application therefore rolled its symlink
back and carried on serving the broken release.

The initial restart was also fatal under `set -e`, so a service that failed to
start exited the script before the rollback branch it was supposed to trigger.

Both are fixed by a single `restart_app()` used by both paths, which never
aborts the script, plus a `roll_back()` that restarts and then *re-verifies*
the restored release - reporting honestly when both releases are unhealthy,
because that is not a release problem.

## The two progress checks share one rule

`uat workflow` judged report substance by stripping headings, table rows and
placeholders; the session hook counted raw bytes. A file of repeated `# TODO`
headings was therefore a stub to one and a completed phase to the other - and
the hook is the surface the agent actually reads.

The hook now applies the same filter in `sed`/`grep` and the same 80-character
threshold, and a test asserts the two agree on heading-only input.

Separately, a phase whose report exists but whose declared artifact does not is
now reported as a **gap** rather than done. A report claiming completion of
phase 06 without `docs/architecture.md` is not a completed phase, and printing
a warning underneath a green label was too easy to read past.
