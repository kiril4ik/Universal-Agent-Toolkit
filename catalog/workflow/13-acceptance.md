# 13 - Acceptance

Prove the product does what phase 02 and phase 03 said it would - by doing it,
against a running system.

<EXTREMELY-IMPORTANT>
"All tests pass" is not acceptance. The tests were written by the same agent
that wrote the code, against the same understanding, and they cover tasks
rather than journeys.

**Acceptance is: every user journey defined in `docs/screens.md` was performed
end to end, through the browser, the backend and the database, and the result
was observed.** Anything not performed is listed as NOT VERIFIED. It is never
assumed to work because the code looks right or a page rendered.
</EXTREMELY-IMPORTANT>

Skip only when there is no product to accept - a library, a script, a Task-class
change whose own verification already covered it.

## Where the checklist comes from

You do not invent it. It already exists:

| Source | Gives you |
|---|---|
| `docs/screens.md` | the journeys, and the five states per screen |
| `docs/business-logic.md` | the rules and invariants that must hold |
| `docs/business-logic.md` | the permission matrix - who may do what |
| `docs/architecture.md` | the invariant-to-enforcement map from phase 06 |

Every journey in that first row must appear in your acceptance table. A journey
that is missing from the table is a failed acceptance, not an oversight.

## How to exercise a journey

Read `../core/VERIFICATION.md`, section "Rendered is not the same as works".
The four rules there are the method:

1. **Drive it.** Fill the form, submit, follow the redirect. Playwright MCP.
2. **Observe through a different path.** Reload, fresh session, or query the
   database directly. Client-side state is not persistence.
3. **Test the denial.** Every permission, from both sides.
4. **Take the unhappy path.** At least once per journey.

## The journeys that rot quietly

Demos cover sign-up and the main screen. These are the ones that ship broken,
so they are named explicitly - check each one that exists in this product:

- **Password reset**, end to end, including an expired or reused token
- **Sign-out**, then confirming protected pages are actually protected
- **Permissions**, per role, from both directions
- **Payment**: success, decline, retry, and what the user sees each time
- **Email/notification** actually sent, and the link in it actually working
- **Empty state** on a genuinely empty account, not a seeded one
- **Second user**: two accounts cannot see each other's data
- **Reload mid-flow**, and the back button
- **A destructive action**: does the confirm work, and is the deletion the
  behaviour the business rules specified (soft, hard, cascade)?

## Invariants, not just journeys

For each rule in `docs/business-logic.md`, name the test that proves it and
show it failing when violated. A rule with only a happy-path test is not
enforced - it is coincidence. "Stock cannot go negative" needs a test that
tries to make it negative.

## Evidence

For each row: the command or URL, what you did, and what you observed. Paste
output. "Looks right" is not evidence, and neither is a screenshot on its own -
see `../core/VERIFICATION.md`.

## Output

`docs/acceptance.md`, plus `.agent-toolkit/reports/13-acceptance.md`:

```markdown
| # | Journey (from screens.md) | How exercised | Evidence | Result |
|---|---|---|---|---|
| 1 | Sign up -> verify email -> first login | Playwright, then reloaded in a fresh session | 3 steps, user row present after reload | PASS |
| 2 | Password reset with expired token | Playwright, token aged in DB | rejected with the specified message | PASS |
| 3 | Payment decline -> retry | not exercised - no test card configured | — | **NOT VERIFIED** |
```

Then state plainly:

- how many journeys were defined, exercised, passed
- **every NOT VERIFIED row, and why** - this is the most important part of the
  report and must never be omitted to make the table look complete
- every invariant without a negative test

## What this phase cannot do

It cannot prove the product is correct. It proves the journeys you defined were
performed and observed to behave as specified. Undefined journeys, unstated
requirements and load behaviour are all outside it - say so rather than letting
a green table imply more than it earned.
