# The planning workflow

Fourteen phases that take a project from an idea to running, accepted code —
and pick up an existing codebase safely.

It is installed at `.agent-toolkit/workflow/` and written for *any* coding
agent. Nothing in it needs a particular tool's features; where a tool has
something better, that is an accelerator, not a requirement.

The canonical text is
[`catalog/workflow/README.md`](../catalog/workflow/README.md). This page is
the orientation.

## The one rule

**No implementation before the gate in phase 11 passes and a human
approves.** Everything before the gate is cheap to change. Everything after
it is expensive.

And at the other end: **"the tests pass" is not the finish line.** Phase 13
performs every journey defined in phase 03 against a running system.

These two bookends never scale away. What you *present* at the gate scales
with the size of the work — a one-line fix gets a sentence — but the stop
itself does not.

## Triage decides how much applies

Phase 00 classifies the work. Running fourteen phases on a one-line fix is
the failure this exists to prevent.

| Class | What it is | Phases it runs |
|---|---|---|
| **Task** | a bounded change to a flow already in this repo | `01`, short design, **`11`**, implement |
| **Feature** | a new capability inside an existing product | `01` `02` `03` `06` `10` **`11`** `12` `13` |
| **Product** | a new project, or a structural change | all of them |

The agent announces the classification and what it is skipping, with the
reason. The class only ratchets **up**: discovering hidden complexity means
stopping and saying so, never quietly continuing at the lower class.

**Phase 11 appears in every row.**

## The phases

| # | Phase | Produces | Skill it delegates to |
|---|---|---|---|
| 00 | Triage | class + phase list | — |
| 01 | Discovery | `.agent-toolkit/reports/01-discovery.md` | — |
| 02 | Business logic | `docs/business-logic.md` | `brainstorming` |
| 03 | Screens & flows | `docs/screens.md` | — |
| 04 | Stack | `docs/stack.md` | — |
| 05 | Rules | installed rule packs | — |
| 06 | Architecture | `docs/architecture.md` | `brainstorming` |
| 07 | Content | `docs/content/` | `writing-guidelines` |
| 08 | Design | `docs/design/` | `ui-ux-pro-max`, Figma MCP |
| 09 | Environments | Docker + deploy config | — |
| 10 | Plan | `docs/superpowers/plans/…` | **`writing-plans`** |
| 11 | **Gate** | go / no-go | — |
| 12 | Execute | working code | **`subagent-driven-development`** |
| 13 | **Acceptance** | `docs/acceptance.md` | Playwright MCP |

### Why design comes after architecture

Screens and flows (03) capture *what* each screen shows and where the data
comes from. That is what architecture needs, and it arrives early.

Visual design (08) then runs against decisions already made: the component
library chosen in the stack phase, and a data model that can actually serve
the screens. Designing before those are settled produces beautiful screens
the data model cannot fill — and the design gets redone.

### Phase 05 closes the loop on the toolkit itself

Once the stack is decided, the workflow tells the agent to run:

```bash
uat detect  --project .
uat install --project . --agent <id> --add <pack>
```

So you start with core packs and grow into the stack you actually chose,
rather than the one you guessed at install time. See
[Packs & profiles](PACKS.md).

### Phase 13 is not "the tests pass"

Acceptance performs every journey from phase 03 against a running system.
Tests written by the agent that wrote the code cover *tasks*; they can all
pass while password reset is broken end to end. A rendered page is not a
working flow.

Anything not actually exercised is reported as **NOT VERIFIED** rather than
assumed. See
[Architecture](ARCHITECTURE.md#acceptance-is-separate-from-verification).

## It sequences Superpowers rather than competing with it

**Phases own the sequence and the gates. Skills own the technique inside a
phase.** When a skill's instructions and the workflow disagree, that single
rule decides it.

Phase 10 does not define a plan format — it hands over to `writing-plans`, so
there is one plan, in one place, that the execution skills can find. Phase 12
hands over to `subagent-driven-development`.

Because the skills were written to run standalone, four of their instructions
are superseded inside the workflow:

1. **Classify once, in triage.** `brainstorming` opens by classifying work.
   You already did that in phase 00 — carry the class in, do not re-derive it.
2. **Batch questions.** `brainstorming` says one question per message; the
   workflow says batch them, because it also runs on agents with no
   interactive turn-taking. The single exception is genuinely exploratory
   design in phases 02 and 08 when the mode is `thorough`.
3. **One stop, not two.** `brainstorming` has its own approval gate, and so
   does phase 11. They are the same requirement; you stop once.
4. **Terminal states do not apply.** `brainstorming` says the only skill after
   it is `writing-plans`. Here, phases 03–09 sit between them.

Everything else is obeyed unmodified — the hard gate, separating facts from
assumptions, YAGNI, `writing-plans`' format and default location,
`test-driven-development`, `verification-before-completion`, and every gate
in `core/SAFETY.md`.

The complete list is the "Precedence" section of
[`catalog/workflow/README.md`](../catalog/workflow/README.md), and the test
suite asserts it covers every known conflict. **No vendored file is edited to
achieve this.**

## Where documents live

Two trees, deliberately:

```
docs/                      product decisions - these outlive the toolkit
  business-logic.md  screens.md  stack.md  architecture.md
  content/  design/
docs/superpowers/plans/    the implementation plan (the skill's own default)
.agent-toolkit/reports/    one short report per completed phase
```

Do not relocate the plan. The execution skills look for it where
`writing-plans` puts it.

Product decisions live in `docs/` because they are yours. Uninstalling the
toolkit does not take your architecture document with it.

## Two entry points

**New project** — start at phase 00 and run the sequence.

**Existing project** — start at phase 01. Discovery answers from the
repository what would otherwise be asked. Then run only the phases whose
artifacts are missing or stale, and read `.agent-toolkit/reports/` before
re-planning anything.

## How you start it

Installing generates the trigger, not just the documentation.

**Claude Code** gets real slash commands:

```
/plan <what you want to build>    run the workflow from triage
/plan-status                      show progress without advancing
/plan-resume                      pick up where it stopped
```

**Every other agent** gets the same instruction as a prompt in
`.agent-toolkit/START-HERE.md`:

> Read `.agent-toolkit/workflow/README.md` and run the planning workflow.
> Start with triage, tell me the classification and which phases apply, then
> work through them in order. Stop at the gate for my approval.

## Checking progress

```bash
uat workflow --project .
```

```
  done  01  discovery              reports/01-discovery.md
  done  02  business logic         docs/business-logic.md
  next  03  screens & flows        docs/screens.md
    -   04  stack                  docs/stack.md
```

Progress lives in `.agent-toolkit/reports/`, one short report per completed
phase, so it survives across sessions, agents and machines. That is what
makes `/plan-resume` work — and what lets a different agent pick the project
up next week without re-deriving everything.

## Interaction mode

The mode is recorded in `.agent-toolkit/project.json` and changes question
*frequency only*. It never weakens a safety gate. See
[Core policy](CORE-POLICY.md#interaction-modes).

## Related

- [Core policy](CORE-POLICY.md) — the rules that apply in every phase
- [Troubleshooting](TROUBLESHOOTING.md) — when the agent skips the workflow
- [Architecture](ARCHITECTURE.md#composing-with-superpowers-instead-of-competing-with-it)
