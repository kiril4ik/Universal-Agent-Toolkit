# Verification

## The rule

**Never claim work is done, fixed, passing, or working without having run
something that proves it and read the output.**

"It should work now" is not a result. "I ran `pnpm test`, 48 passed, 0
failed" is a result.

## Before saying "done"

Run the checks that actually apply to what you changed, and paste the
relevant output:

| You changed | You must run |
|---|---|
| Application logic | the test suite, or the specific tests covering it |
| A bug fix | a test that fails before the fix and passes after |
| Types / interfaces | the type checker or compiler |
| Anything at all | the linter and formatter, if the project has them |
| A UI change | drive the flow in a browser - not a screenshot (see below) |
| A migration | the migration up, then the app, then the rollback |
| A Dockerfile / compose file | a real build and start, then a health check |
| A deploy script | a dry run, then a run against a disposable target |

If the project has no test for what you changed, say so explicitly rather
than implying coverage exists.

## Rendered is not the same as works

A screenshot proves a page rendered. It proves nothing about whether the
thing the page is *for* actually happens. A convincing dashboard can sit on
top of a broken password reset, a permission check that never runs, or a
payment retry that silently drops.

So for anything a user does, not just looks at:

**Drive the flow, do not photograph it.** Fill the form, submit it, follow the
redirect, and check the result. The Playwright MCP exists for this.

**Observe the effect through a different path than the one that caused it.**
Creating a record through the UI and then seeing it in the UI can pass on
client-side state alone. Reload the page, open a fresh session, or query the
database. If the data does not survive a reload, it was never saved.

**Test the denial, not only the permission.** "The admin can see it" is half a
check. The half that matters for security is that the non-admin cannot.

**Exercise the unhappy path at least once.** Wrong password, expired token,
declined card, duplicate submit, network failure mid-flow. These are where
real products break, and they are never the path you demo.

## Honest reporting

- If tests fail, report the failure and the output. Do not describe the
  work as complete "apart from" a failing test.
- If you skipped a step, say which and why.
- If you could not verify something, say that plainly. An unverified
  change described as verified is worse than an unverified change.
- Never state a number you did not read from output. Do not estimate
  coverage, test counts, timings, or bundle sizes from memory.

## Red flags in your own reasoning

| Thought | What to do instead |
|---|---|
| "This is a trivial change, it can't break" | Run the check. It takes seconds. |
| "The test would probably pass" | Then running it costs nothing. Run it. |
| "I'll just say it's done and fix it if they complain" | This is the failure mode this file exists to prevent. |
| "The build was passing before my change" | It was. Confirm it still is. |
| "I can't run it in this environment" | Say so explicitly in your report. |

## Verification commands belong in the plan

Every task in an implementation plan states its own verification command
before implementation starts. If you cannot name the command that will
prove a task is finished, the task is not specified well enough to start.
