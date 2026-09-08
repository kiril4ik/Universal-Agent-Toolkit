# 02 - Business logic

Define what the software must actually do, in domain terms, before anyone
talks about frameworks or screens.

Skip for task-class work. Never skip for product-class work.

**Use the `brainstorming` skill for this phase** - announce it, and read
`../skills/brainstorming/SKILL.md`. It supplies the technique: separating
facts from assumptions from unknowns, proposing real alternatives, and
YAGNI-ing speculative scope.

Two of its instructions are superseded here - carry your triage class in
rather than re-classifying, and batch your questions unless the mode is
`thorough`. See "Precedence" in `README.md`.

## Establish the frame

- **What problem does this solve, for whom?** One paragraph, concrete.
- **What does success look like?** Something measurable, not "users like it".
- **What is explicitly out of scope?** This is as important as what is in.
  Write it down; it is the thing that prevents scope creep later.

## Then the domain

**Actors and roles.** Every kind of user and system that interacts with this.
For each: what they can see, what they can do, what they must never do.

**Entities and relationships.** The nouns of the domain, their meaningful
fields, and how they relate. Cardinality matters - "a user has many orders"
and "an order has many users" are different products.

**State and transitions.** For anything with a lifecycle (order, subscription,
document, ticket): the states, the legal transitions, who can trigger each,
and what happens on failure halfway through.

**Rules and invariants.** The things that must always be true. "An invoice
cannot be edited after it is sent." "Stock cannot go negative." These become
your most valuable tests.

**Permissions.** Who can do what, to which records. Be explicit about the
difference between "can see the page" and "can see this row".

## The parts people forget

Ask about these directly; they are where projects die:

- **Money.** Currency, rounding, tax, refunds, partial payments, failed payments.
- **Time.** Time zones, "day" boundaries, scheduling, expiry, retention.
- **Deletion.** Soft or hard? What happens to related records? Legal retention?
- **Concurrency.** What if two people act on the same record simultaneously?
- **Volume.** How many records, how many users, how fast is it growing?
- **Compliance.** Personal data, payment data, health data, audit trails.
- **Failure.** What happens when an external service is down? Retry? Queue? Fail?

## Output

`docs/business-logic.md` - actors, entities, relationships, state machines,
rules, permissions, and an explicit out-of-scope list.

Plus `.agent-toolkit/reports/02-business-logic.md` recording decisions,
assumptions made, and questions still open.
