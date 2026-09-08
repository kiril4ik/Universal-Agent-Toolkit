# 10 - Implementation plan

Turn everything above into an ordered list of independently verifiable tasks.

Skip for task-class work - implement it directly, with tests.

## What a task looks like

Each task states, before implementation starts:

- **Goal** - one sentence, in terms of observable behaviour
- **Depends on** - which tasks must be done first
- **Files** - the specific files to create or change
- **Approach** - enough that someone else could implement it the same way
- **Tests** - what proves it works, written before or alongside the code
- **Verification command** - the exact command, and what passing looks like
- **Done when** - acceptance criteria a reviewer can check

If you cannot name the verification command, the task is not ready.

## Slice vertically

Prefer thin end-to-end slices over horizontal layers. "The whole data layer"
is not demonstrable and hides integration problems until the end. "A user can
sign up and see their empty dashboard" is demonstrable on day one and proves
the layers actually connect.

Order so that something runs as early as possible, and stays running.

## Size

A task should be completable and verifiable in one focused sitting. If a task
has "and" in its goal, it is probably two tasks. If it touches fifteen files,
it is definitely more than one.

## Sequence deliberately

Put first: anything that proves a risky assumption, anything everything else
depends on, and anything that would force rework if discovered late.

Put last: polish, optimisation, and anything you might not need.

## What goes in the plan that is not a feature

Be explicit about these, or they never get done:

- Project setup, tooling, CI
- The Docker environment from phase 09
- Authentication, if there is any
- Error handling and logging
- The deployment path, exercised at least once before it is needed
- Seed data from phase 04

## Output

`docs/plan.md` - the ordered task list, in the format above.

Plus `.agent-toolkit/reports/10-plan.md` recording sequencing rationale and
identified risks.

## Executing it

If your tool has a plan-execution skill (Superpowers `executing-plans`,
`subagent-driven-development`), use it. Otherwise work the list in order:
implement one task, run its verification command, read the output, commit,
move on. One task per commit.
