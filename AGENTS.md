# Universal Agent Toolkit — instructions for agents working on this repository

This repository is a **toolkit that configures other projects**. It is not an
application. Changes here affect every project the toolkit is installed into.

## Before changing anything

1. Read `README.md` and `docs/ARCHITECTURE.md`.
2. Run `./bin/uat doctor` and `./bin/uat-test` so you know the starting state.

## The rules that matter most

**`vendor/` is never edited.** Those are verbatim upstream snapshots, verified
by content hash. If an upstream is wrong, add an overlay in `catalog/packs/`
or record our own policy in `catalog/core/`. Editing a snapshot makes
`uat vendor verify` fail, which is the point.

**Never fabricate provenance.** If `SOURCE.json` says a file came from a
commit, it must have been fetched from that commit. Do not write content from
memory and label it as vendored. This is the specific failure the rewrite of
this repository existed to correct.

**Tool-specific knowledge belongs in `catalog/agents.json`**, not in code. If
a tool changes its config format, that is a data edit.

**Adapters are pointers.** Generated tool files route to
`.agent-toolkit/CORE.md`. Never inline rule bodies into an always-loaded file
— that is context bloat in every project, forever.

**The installer never overwrites without `--force`.** Anything that changes a
target project must go through `util.write_text` / `copy_file` so `--dry-run`
and conflict reporting keep working.

## Layout

```
bin/uat            launcher (bash -> python3, no install step)
src/uat/           implementation, standard library only
catalog/
  agents.json      agent surface registry  <- tool formats live here
  vendor.json      upstream pins
  core/            our always-on policy (safety, git, verification, modes)
  workflow/        the project planning workflow
  packs/<id>/      installable units
  profiles/        named pack bundles
vendor/<id>/       verbatim snapshots + SOURCE.json
tests/             the test suite
```

## Verification

Before claiming any change here is complete:

```bash
./bin/uat-test        # 161 tests
./bin/uat doctor      # catalog + registry + vendor integrity
./bin/uat install --project /tmp/probe --agent claude-code --yes --dry-run
```

Bash in `catalog/packs/deploy-ubuntu/` must pass `bash -n`, and ideally be
exercised in an `ubuntu:24.04` container before you claim it works.

## Git

Atomic commits, conventional messages, and **no AI attribution** — no
`Co-authored-by`, `Generated-by`, or model names, unless explicitly asked.
See `catalog/core/GIT.md`.
