# 10 - Implementation plan

**This phase does not define a plan format. It hands over to the
`writing-plans` skill, which does.**

Skip for task-class work.

## Use the skill

**Announce:** "I'm using the writing-plans skill to create the implementation plan."

Read `../skills/writing-plans/SKILL.md` and follow it exactly. It is more
rigorous than anything this workflow would restate: file-structure mapping
before task decomposition, task right-sizing, bite-sized steps carrying their
own TDD cycle, a no-placeholders rule, and a self-review pass for spec
coverage and type consistency.

Do not write your own plan format alongside it. One plan, one format.

## What this workflow supplies as the spec

`writing-plans` expects a spec. Yours is not a single file - it is the set of
artifacts the earlier phases produced:

| Skill expects | You have |
|---|---|
| requirements | `docs/business-logic.md` |
| interface surface | `docs/screens.md` |
| technical constraints | `docs/stack.md`, `docs/architecture.md` |
| environment | `.agent-toolkit/deploy/`, `.agent-toolkit/docker/` |
| decision history | `.agent-toolkit/reports/` |

Read all of them before starting. When the skill's spec-coverage check asks
whether every requirement maps to a task, check it against **all** of these,
not just the last one you read.

## Where the plan goes

Use the skill's own default: `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`.

Do not relocate it. The execution skills look there, and a plan in a bespoke
location is a plan that the execution chain cannot find.

## What this workflow adds that the skill does not

The skill plans a feature. This workflow is planning a *project*, so make sure
the plan also contains the work that is nobody's feature and therefore never
gets written down:

- project setup, tooling, linting, CI
- the Docker environment from phase 09
- authentication, if there is any
- error handling and logging as a deliberate task, not a side effect
- the deployment path, exercised once before it is needed
- seed data from phase 07

If any of these is missing from the plan after the skill's self-review, add it.

## Sequencing

Order so something runs end to end as early as possible and stays running.
Prefer thin vertical slices over horizontal layers: "a user can sign up and
see an empty dashboard" is demonstrable on day one and proves the layers
connect. "The whole data layer" is neither.

Put first anything that proves a risky assumption or that everything else
depends on. Put last polish, optimisation, and anything you might not need.

## Output

`docs/superpowers/plans/YYYY-MM-DD-<feature>.md` - written by the skill.

Plus `.agent-toolkit/reports/10-plan.md` recording sequencing rationale, the
risks you identified, and anything you added beyond the skill's output.

## Next

Phase 11. **Do not accept the skill's execution handoff yet** - it will offer
you subagent-driven or inline execution. The gate comes first.
