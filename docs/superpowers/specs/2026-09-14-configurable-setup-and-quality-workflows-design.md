# Configurable Setup and Quality Workflows Design

## Goal

Make installation explicit and configurable for new and existing projects while
keeping the current pack architecture. Add Ponytail as a default, deselectable
pack; strengthen downstream acceptance, visual validation, database backup, and
image-generation guidance; and repair serious installer defects found during the
repository audit.

## Scope

This change implements the approved priority-one setup choices:

1. project type;
2. coding agents;
3. interaction mode;
4. planning workflow depth;
5. technology-pack installation policy;
6. acceptance-testing depth;
7. visual validation;
8. database completion backups;
9. Codex-assisted image generation;
10. default engineering skills;
11. detected technology rules;
12. browser and quality tools;
13. design and content tools;
14. infrastructure tools;
15. an exact final installation summary.

It also fixes stale content left by `--replace`, stale surfaces for removed
agents, machine-specific paths in embedded metadata, incorrect workflow phase
references, and incomplete embedded dry-run previews.

## Progressive interactive setup

Running `uat install --project PATH` in a terminal is sufficient. The installer
asks, in order:

1. **Project type** — use the detected value, or choose `new` / `existing`.
2. **Coding agents** — choose one or more when `--agent` was not supplied.
3. **Interaction mode** — `thorough`, `focused`, or `autonomous`.
4. **Planning** — `adaptive`, `full`, or `off`.
5. **Automation policies** — technology additions, acceptance, visual checks,
   database backups, and image generation. Each prompt includes a one-line
   consequence and a safe default.
6. **Capabilities** — the existing keyboard picker, grouped by purpose:
   engineering, technology, browser/quality, design/content, infrastructure,
   and integrations. Default and detected packs are preselected but every pack,
   including Ponytail, is deselectable.
7. **Review** — exact rules, skills, MCP servers, hooks, workflow files, and
   external agent files, followed by one `Proceed?` prompt.

Existing installations preserve their recorded answers unless the user supplies
new flags or chooses `--replace`.

Non-terminal use never prompts. Every interactive answer has a CLI equivalent:

```text
--project-kind {auto,new,existing}
--mode {thorough,focused,autonomous}
--planning {adaptive,full,off}
--technology-additions {ask,auto,off}
--acceptance {full,browser,off}
--visual-validation / --no-visual-validation
--db-backups {finish,risky,off}
--image-generation {ask,auto,off}
--agent ID (repeatable)
--packs ID... / --profile NAME / --all
```

`--yes` uses documented defaults and requires `--agent`; it does not invent an
agent choice. Explicitly passing `--packs` with no values selects no packs.

## Stored project policy

`.agent-toolkit/project.json` records the answers under stable keys:

```json
{
  "project_kind": "existing",
  "mode": "focused",
  "planning": "adaptive",
  "technology_additions": "ask",
  "acceptance": "full",
  "visual_validation": true,
  "db_backups": "finish",
  "image_generation": "ask"
}
```

Defaults are `auto`, `focused`, `adaptive`, `ask`, `full` for detected frontend
projects and `browser` otherwise, visual validation on for detected frontends,
`finish`, and `ask`. `auto` project kind resolves to `new` or `existing` before
being stored.

The generated router summarizes active policies. Workflow files read the same
keys and must not silently override them.

## Planning and technology additions

Planning is optional:

- `adaptive` installs the workflow and lets triage skip irrelevant phases;
- `full` installs it and requires all applicable product phases;
- `off` installs no workflow directory, report scaffold, `START-HERE.md`, or
  planning slash commands.

`uat detect --recommend` prints detected technologies, the evidence for each,
matching packs, and the exact rules, skills, and MCP servers those packs add.
The rules phase behaves according to `technology_additions`: show and ask,
install automatically, or report recommendations without installing. This
phase remains optional and refers to phases by name rather than duplicating
numbers in prose.

## Pack groups and Ponytail

Packs gain an optional `category` field. Unspecified packs default to
`technology`. The picker uses the six categories in the progressive setup.

Ponytail is pinned to an exact upstream commit under `vendor/ponytail/`. The
snapshot includes `AGENTS.md`, `skills/`, `LICENSE`, and `README.md`. A core-tier
`ponytail` pack installs `AGENTS.md` as the always-on `rules/PONYTAIL.md` and
all six upstream skills. Core means selected by default on the recommendation
path, not mandatory; the picker labels it `default`, and an explicit pack list
still remains exact.

## Acceptance and visual validation

Existing Playwright support is extended rather than duplicated.

When acceptance is `full`, every journey from `docs/screens.md` is driven end
to end against the running product. Persistence, denial, and at least one
unhappy path are observed independently. `browser` requires browser verification
for affected flows without demanding the complete story inventory. `off`
disables the workflow acceptance phase but never permits false verification
claims.

When visual validation is enabled, Playwright captures every documented page
and applicable empty/loading/error/full state at 390×844, 768×1024, and
1440×900, plus project-specific breakpoint-adjacent widths. Evidence is stored
under `docs/acceptance/screenshots/`. The agent checks overflow, clipping,
overlap, missing content/actions, console errors, and design fidelity. A
screenshot validates layout only; functional stories must still be driven.

## Database completion backups

Database-backed projects using `db_backups=finish` create a repository-local
dump after final tests and before completion is claimed. Dumps go to
`backups/db/` with timestamp, environment, engine, and database name in the
filename. The directory is ignored by Git because dumps may contain secrets or
personal data. Persistent development and persistent test databases are
included. Disposable test databases are exempt and reported as such.

`risky` retains only the existing pre-destructive-change backup gate. `off`
disables the completion dump but not destructive-action approval. A missing
database client, unavailable database, or failed dump is reported honestly and
prevents a claim that the backup completed.

## Codex-assisted image generation

A `codex-image-generation` pack installs an authored rule. It is recommended
for detected frontend projects and included in the design profile, but remains
deselectable. The rule checks `codex --version`, then performs a minimal
non-mutating response probe before relying on `codex exec`. It uses `$imagegen`
for raster assets such as hero images, backgrounds, content illustrations, and
logo/icon exploration when no established vector system should be extended.

The rule requires an explicit destination inside the project, inspection of the
generated result, preservation of existing assets unless replacement was
requested, and honest fallback when Codex is unavailable.

## Safe replacement and audit fixes

Before a real replacement install, the engine compares the previous ownership
manifest with the desired plan:

- unchanged toolkit-owned files no longer desired are removed;
- modified files are preserved and reported as conflicts;
- user-owned files are never removed;
- dropped agents lose only surfaces recorded as toolkit-owned;
- shared MCP and hook files are edited surgically;
- removed packs no longer remain in the router or state.

Dry-run reports the same removals without changing disk. `--embed --dry-run`
also previews embedded files and vendor depth. `--with-vendor` without
`--embed` is rejected. Embedded metadata records a portable source label, not
the originating machine's absolute path.

Generated workflow summaries use phase names. Numbered filenames remain the
single ordering mechanism, avoiding a second phase-number map that can drift.

## README diagram

The existing `docs/assets/simple-scheme.png` is regenerated because its mandatory planning
step would contradict the new `planning=off` path. The replacement shows target
selection, behavior choices, capability selection, exact review, an optional
planning branch, implementation, and verification/backups. README uses the
image near the getting-started flow.

## Verification

Every behavior is introduced test-first in `tests/test_uat.py`. Completion
requires:

```bash
python3 -m compileall -q src tests
find catalog/packs -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n
./bin/uat-test
uat doctor
uat install --project /tmp/probe --agent claude-code --yes --dry-run
```

Vendor verification must prove the Ponytail bytes match the pinned commit.
The generated diagram is inspected at original resolution before it is linked
from README.
