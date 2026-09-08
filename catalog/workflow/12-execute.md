# 12 - Execute

Only after the gate in `11-gate.md` has passed **and a human has approved.**

This phase, like phase 10, delegates. Superpowers has a complete execution
chain and this workflow does not restate it.

## Choose an execution mode

`writing-plans` ends by offering two options. Take that offer now:

**Subagent-driven (preferred where subagents exist)**
`../skills/subagent-driven-development/SKILL.md` - a fresh subagent per task
with two-stage review. Each task starts with clean context, which is why it
holds quality over a long plan.

**Inline**
`../skills/executing-plans/SKILL.md` - execute in the current session with
checkpoints. Use when subagents are unavailable.

Announce which you are using and why.

## Isolate the workspace first

Both paths expect an isolated workspace. Use
`../skills/using-git-worktrees/SKILL.md` to create or verify one before the
first task. Do not start implementing on the branch your human is sitting on.

## While executing

- One task at a time. Mark it in progress, follow its steps exactly, run its
  verification, mark it done.
- `../skills/test-driven-development/SKILL.md` governs how each task is built.
- `../core/VERIFICATION.md` governs when you may call it done. Run the
  command, read the output. "Should work" is not a result.
- One coherent commit per task - see `../core/GIT.md`.

## Stop immediately when

- a task hits a blocker: missing dependency, failing test you did not cause,
  an instruction you do not understand
- the plan turns out to have a gap that prevents starting
- something in the plan would touch production-like data and the backup gate
  in `../core/SAFETY.md` has not been satisfied

Stopping and asking is cheap. Improvising past a blocker is how a plan quietly
stops describing the code.

## Debugging

When something breaks, use `../skills/systematic-debugging/SKILL.md` before
proposing a fix. Do not guess, and do not "try things" - that is how one bug
becomes three.

## Finishing

When every task is done and verified, use
`../skills/finishing-a-development-branch/SKILL.md` to verify the suite,
present the integration options and execute the choice.

## Output

Working, verified code, and `.agent-toolkit/reports/12-execute.md` recording
what was built, what deviated from the plan and why, and what remains.

## Next

Phase 13. **Do not report the product as finished yet.** A green test suite
means the tasks were completed; it does not mean the journeys work. Acceptance
performs them.
