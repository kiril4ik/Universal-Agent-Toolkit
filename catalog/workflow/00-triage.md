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

If the work is genuinely small, ask once - and **put the design in the
question**, so the answer is a decision about what you will actually do:

> This looks like Task-class work: <what you will change, which files, how you
> will test it>. The full planning sequence would cost more than the change,
> so I'd implement it directly with a test. Shall I?

A yes to that is the phase 11 approval for Task work: you presented the design
and a human decided. There is no separate gate afterwards - see `11-gate.md`.

A no means run more of the sequence.

Ask this **once**. Do not re-ask every phase. And do not ask it without the
design - "shall I just do it?" is not something anyone can approve.

## Classify once

`brainstorming` will ask you to classify again in its own words. **Do not.**
Carry the class you decided here, and say so:

> Triage classified this as Feature, which maps to Bounded. Using that.

| Here | brainstorming |
|---|---|
| Task | Bounded |
| Feature | Bounded, or Architectural when it changes an interface others depend on |
| Product | Architectural |
| a probe inside phase 01 or 04 | Spike |

Re-deriving the class is not free: it is how a one-line change ends up on the
architectural path, which is the outcome this phase exists to prevent.

## Red flags

| Thought | Reality |
|---|---|
| "I understand this kind of app, so it's a Task" | Task measures the repo, not your familiarity. If the flow isn't here to read, it isn't a Task. |
| "I'll decide the class as I go" | Then you will decide it under pressure, badly. Decide now, in one line. |
| "It grew, but I'm nearly done" | The class ratchets up. Stop and say so. |
| "They approved the last one, so this is approved" | Each piece of work gets its own class and its own approval. |

## The ratchet

Class only goes up. If, midway, you find hidden complexity - an undocumented
integration, a data migration, an auth change - stop, say the class has
increased, and pick up the phases you skipped. Never quietly continue with a
process that no longer fits.

## Output

One line in your next message stating class, phases you will run, and phases
you are skipping with the reason. No report file for this phase.
