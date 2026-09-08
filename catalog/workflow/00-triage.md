# 00 - Triage

Decide how much process this work deserves, and say the answer out loud
before doing anything else. The human can then override you cheaply.

## Classify

**Task** - a bounded change to a flow that already exists in this repository.
A new flag, one endpoint, a copy change, a bug fix.

> Bounded is measured against the repository, not against your confidence.
> "I understand how apps like this work" is not bounded. If the flow you are
> about to change is not already here to read, this is not a task.

**Feature** - a new capability inside an existing product. New screens or new
endpoints, but the architecture and stack stay as they are.

**Product** - a new project, or a change that restructures how components fit
together, or that changes an interface other people depend on.

## Announce it

Say something like:

> This looks like Feature-class work, so I will run discovery, business logic,
> screens, architecture and the plan, then stop at the gate. Skipping content
> and design because this is an internal API with no UI. Tell me if you want
> the full sequence instead.

## Size check for very small work

If the work is genuinely small, ask once:

> This is small enough that the full workflow would cost more than the change.
> I suggest going straight to implementation with tests. Do you want the
> full planning sequence anyway?

Ask this **once**. If the answer is no, proceed. Do not re-ask every phase.

## The ratchet

Class only goes up. If, midway, you find hidden complexity - an undocumented
integration, a data migration, an auth change - stop, say the class has
increased, and pick up the phases you skipped. Never quietly continue with a
process that no longer fits.

## Output

One line in your next message stating class, phases you will run, and phases
you are skipping with the reason. No report file for this phase.
