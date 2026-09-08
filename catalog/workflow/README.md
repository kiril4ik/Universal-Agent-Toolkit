# Project workflow

The sequence for taking a project from idea to running code, and for
picking up an existing codebase safely.

This file is written for *any* coding agent. Nothing here depends on a
particular tool's features. Where a tool has something better (Claude Code
skills, Cursor glob rules), it is an accelerator, not a requirement.

## The one rule

**No implementation before the gate in `11-gate.md` passes.**

Everything before that gate is cheap to change. Everything after it is
expensive. The whole point of the sequence is to move decisions to the
cheap side.

## Triage first - do not run all of this on a one-line change

Read `00-triage.md` and classify the work:

| Class | What it is | What you run |
|---|---|---|
| **Task** | A bounded change to a flow that already exists in this repo | `01`, then implement. No artifacts. |
| **Feature** | A new capability inside an existing product | `01` `02` `03` `05`* `08` `10` `11` |
| **Product** | A new project, or a change that restructures the system | All phases |

\* only when there is a user interface.

If you are unsure between two classes, take the heavier one. Discovering
hidden complexity mid-task upgrades the class - stop and say so. Nothing
downgrades mid-task.

When a phase clearly does not apply (a CLI tool has no design phase, an
internal script needs no content), say which phase you are skipping and
why, then skip it. Announce it; do not silently drop it.

## Phases

| # | Phase | Produces | Skippable when |
|---|---|---|---|
| 00 | [Triage](00-triage.md) | class + phase list | never |
| 01 | [Discovery](01-discovery.md) | `reports/01-discovery.md` | never |
| 02 | [Business logic](02-business-logic.md) | `docs/business-logic.md` | task-class work |
| 03 | [Screens & flows](03-screens-and-flows.md) | `docs/screens.md` | no user interface |
| 04 | [Content](04-content.md) | `docs/content/` | no user-visible copy |
| 05 | [Design](05-design.md) | `docs/design/` + tokens | no user interface |
| 06 | [Stack](06-stack.md) | `docs/stack.md` | stack already fixed |
| 07 | [Rules](07-rules.md) | installed rule packs | stack already covered |
| 08 | [Architecture](08-architecture.md) | `docs/architecture.md` | task-class work |
| 09 | [Environments](09-environments.md) | Docker + deploy scripts | already provisioned |
| 10 | [Implementation plan](10-plan.md) | `docs/plan.md` | task-class work |
| 11 | [Gate](11-gate.md) | go / no-go | **never** |

Paths are relative to the project root. Reports go in
`.agent-toolkit/reports/`; durable project documentation goes in `docs/`
because it outlives the toolkit.

## Interaction mode governs how much you ask

Read `../core/INTERACTION_MODES.md`. The mode is recorded in
`.agent-toolkit/project.json`.

- **thorough** - ask everything that materially changes the outcome
- **focused** - ask only blocking questions, default the rest, record the defaults
- **autonomous** - decide and document; interrupt only for risky or genuinely ambiguous calls

The mode changes *question frequency only*. It never weakens the safety
gates in `../core/SAFETY.md`.

## Two entry points

**New project** - start at `00`, run the full sequence.

**Existing project** - start at `01`. Discovery reads the codebase and
fills in what would otherwise be asked. Most answers are already in the
repository; asking for them is how you lose the human's trust. Then run
only the phases whose artifacts are missing or stale.

## Reporting

Every completed phase writes `.agent-toolkit/reports/NN-phase.md` using
`templates/report.md`. Keep them short. Their job is to let a different
agent - or the same agent next week - resume without re-deriving
everything.

## Handling questions

Batch them. Ask several related questions in one message rather than
interrogating one at a time. Never ask something the repository answers.
State your assumption when you proceed without an answer, and put it in
the report so it can be corrected later.
