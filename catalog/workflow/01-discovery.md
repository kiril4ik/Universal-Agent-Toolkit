# 01 - Discovery

Understand what already exists before proposing anything. This phase is
never skipped, including for new projects (where its finding is "empty
directory", which is itself worth stating).

## Read before you ask

Work through whatever is present:

- `README`, `docs/`, `CONTRIBUTING`, architecture decision records
- package manifests and lockfiles - the real dependency list, and versions
- `.env.example` - the real integration surface
- Docker / compose files, CI config, deployment scripts
- database migrations - the real data model, in change order
- routes / controllers / page files - the real feature list
- tests - the real specification, and the real coverage level
- recent `git log` - what the team is actually working on, and their commit conventions
- existing agent config: `.agent-toolkit/`, `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`

## For an existing codebase, also determine

- **Conventions in use.** Naming, file layout, error handling, test style.
  You will follow these, not your preferences.
- **The state of the tests.** Do they pass right now? Run them. A suite that
  was already red changes how you verify your own work.
- **Data model reality.** Migrations plus the live schema if reachable.
- **What is load-bearing.** Which modules would be expensive to get wrong.
- **Dead ends.** Abandoned code, disabled features, TODOs that reveal
  known problems.

## Separate three things

Keep these distinct in the report and never let them blur:

- **Facts** - things you read in the repository. Cite the file.
- **Assumptions** - things you believe but have not confirmed. Each one needs
  an owner: either the human confirms it, or you verify it.
- **Unknowns** - things you cannot determine from the repository at all.
  These become the questions for the next phase.

## Verify the environment can run

Before planning changes, establish whether you can actually run this thing:
install dependencies, start it, run the test suite. If you cannot, that is the
first problem to solve and it belongs at the top of the report.

## Output

`.agent-toolkit/reports/01-discovery.md`

Must contain: what exists, stack detected, conventions observed, test status
(with the command and its real output), facts / assumptions / unknowns, and
the questions you need answered to continue.
