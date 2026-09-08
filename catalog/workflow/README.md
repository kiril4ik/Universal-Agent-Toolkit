# Project workflow

Taking a project from idea to running code, and picking up an existing
codebase safely.

Written for *any* coding agent. Nothing here needs a particular tool's
features. Where a tool has something better, it is an accelerator, not a
requirement.

<EXTREMELY-IMPORTANT>
This workflow does not replace the Superpowers skills. It sequences them and
adds the product phases they do not cover.

**Phases own the sequence and the gates. Skills own the technique inside a
phase.**

When a skill's instructions and this workflow disagree, that single rule
decides it. The specific cases are listed under "Precedence" below - read
them once, before you invoke your first skill.
</EXTREMELY-IMPORTANT>

## The one rule

**No implementation before the gate in `11-gate.md` passes and a human
approves.** Everything before the gate is cheap to change. Everything after
it is expensive.

This holds at every class. What you *present* for approval scales - a Task
gets a few sentences, a Product gets the coherence review - but the stop
itself does not scale away.

## Triage first

Read `00-triage.md` and classify. Do not run twelve phases on a one-line fix.

| Class | What it is | Phases |
|---|---|---|
| **Task** | a bounded change to a flow already in this repo | `01`, short design, **`11`**, implement |
| **Feature** | a new capability inside an existing product | `01` `02` `03` `06` `10` **`11`** `12` |
| **Product** | a new project, or a structural change | all |

Announce the classification and what you are skipping, with the reason.
The class only ratchets up: hidden complexity means stop and say so.

**Phase 11 appears in every row.** What you present there scales with the
class - for a Task it is a few sentences, not a coherence matrix - but the
approval itself is never skipped. See `11-gate.md`.

## Phases

| # | Phase | Produces | Skill it uses |
|---|---|---|---|
| 00 | [Triage](00-triage.md) | class + phase list | — |
| 01 | [Discovery](01-discovery.md) | `reports/01-discovery.md` | — |
| 02 | [Business logic](02-business-logic.md) | `docs/business-logic.md` | `brainstorming` |
| 03 | [Screens & flows](03-screens-and-flows.md) | `docs/screens.md` | — |
| 04 | [Stack](04-stack.md) | `docs/stack.md` | — |
| 05 | [Rules](05-rules.md) | installed rule packs | — |
| 06 | [Architecture](06-architecture.md) | `docs/architecture.md` | `brainstorming` |
| 07 | [Content](07-content.md) | `docs/content/` | `writing-guidelines` |
| 08 | [Design](08-design.md) | `docs/design/` | `ui-ux-pro-max`, Figma MCP |
| 09 | [Environments](09-environments.md) | Docker + deploy | — |
| 10 | [Plan](10-plan.md) | `docs/superpowers/plans/…` | **`writing-plans`** |
| 11 | [Gate](11-gate.md) | go / no-go | — |
| 12 | [Execute](12-execute.md) | working code | **`subagent-driven-development`** |

### Why design comes after architecture

Screens and flows (03) capture *what* each screen shows and where the data
comes from — that is what architecture needs, and it comes early.

Visual design (08) then runs against decisions already made: the component
library from the stack, and the data the architecture can actually serve.
Designing before those are settled produces beautiful screens that the data
model cannot fill, and the design gets redone.

## Precedence

Skills were written to be used standalone. Inside this workflow, four of
their instructions are superseded. This is the complete list.

### 1. Classify once, in triage

`brainstorming` opens by classifying work as spike / bounded / architectural.
You already classified in phase 00. **Carry your class in; do not re-derive
it.**

| Phase 00 | brainstorming |
|---|---|
| Task | Bounded |
| Feature | Bounded, or Architectural if it changes interfaces others depend on |
| Product | Architectural |
| *(a probe inside 01 or 04)* | Spike |

### 2. Batch questions

`brainstorming` says one question per message. **This workflow says batch
them**, because it also runs on agents with no interactive turn-taking, where
one-at-a-time is unusable.

The exception, and the only one: genuinely exploratory design in phases 02
and 08 when the interaction mode is `thorough`. There, one at a time is
better and the skill's cadence wins.

### 3. One stop, not two

`brainstorming` has its own approval gate. So does phase 11. They are the same
requirement, and you stop **once**:

- **Task class** — brainstorming's short-design approval *is* phase 11. Present
  the design, get an explicit yes, implement. Do not additionally run a
  coherence review over artifacts that do not exist.
- **Feature / Product** — brainstorming's approval covers its own design
  section as you go; phase 11 is the single stop before implementation, after
  the plan exists.

Never stop twice for approval of the same thing - and never skip the approval
because you already discussed it. Discussion is not approval.

### 4. Terminal states do not apply here

`brainstorming` says the only skill to invoke after it is `writing-plans`.
That is true when it runs standalone. **Here, phases 03 through 09 sit
between them** — that is the product work this workflow exists to add.
Do not skip from brainstorming straight to the plan.

### What is NOT superseded

Everything else. In particular, obey without modification:

- the hard gate: no implementation before approval
- separating facts, assumptions and unknowns
- proposing real alternatives, and YAGNI
- `writing-plans`' plan format and its default location
- `test-driven-development` and `verification-before-completion`
- every gate in `../core/SAFETY.md`

## Where documents live

Two trees, deliberately:

```
docs/                      product decisions - outlive the toolkit
  business-logic.md  screens.md  stack.md  architecture.md
  content/  design/
docs/superpowers/plans/    the implementation plan (skill's own default)
.agent-toolkit/reports/    one short report per completed phase
```

Do not relocate the plan. The execution skills look for it where the skill
puts it.

## Interaction mode

Read `../core/INTERACTION_MODES.md`; the mode is in
`.agent-toolkit/project.json`.

`thorough` asks everything material, `focused` asks only blockers and records
its defaults, `autonomous` decides and documents. The mode changes question
*frequency only*. It never weakens a safety gate.

## Two entry points

**New project** — start at `00`, run the sequence.

**Existing project** — start at `01`. Discovery answers from the repository
what would otherwise be asked. Then run only the phases whose artifacts are
missing or stale. Read `.agent-toolkit/reports/` before re-planning anything.

## Red flags

| Thought | Reality |
|---|---|
| "I'll classify again now that I'm in brainstorming" | You classified in phase 00. Carry it in. |
| "The skill says one question at a time" | Superseded here, except thorough-mode design. |
| "I got approval in brainstorming, so I can implement" | For Task that approval IS the gate. For Feature and Product, phase 11 is the stop. |
| "Task class skips phase 11" | It skips the coherence *review*, never the approval. |
| "I explained what I'd do, so I can start" | Explaining is not asking. Wait for the answer. |
| "Brainstorming says go straight to writing-plans" | That is its standalone path. Phases 03-09 come first. |
| "I'll write my own plan format, it's clearer" | One plan, one format. Use `writing-plans`. |
| "Design first, we can adjust the data model later" | That is the rework this ordering exists to prevent. |
| "This is small, I'll skip triage" | Triage is what makes it small. It takes one line. |
| "The gate is a formality, the plan is obviously right" | The gate is where cheap fixes are still cheap. |

## Reporting

Every completed phase writes `.agent-toolkit/reports/NN-phase.md` from
`templates/report.md`. Keep them short. Their job is to let a different agent,
or you next week, resume without re-deriving everything.

Check progress any time with `uat workflow --project .`.
