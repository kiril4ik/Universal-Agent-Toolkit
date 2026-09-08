# 11 - Gate

The checkpoint before implementation starts. **Never skipped, at any class.**

Its purpose is to catch the cheap-to-fix problems while they are still cheap.

## Check coherence, not completeness

Anyone can tick boxes. The value here is cross-checking artifacts against each
other, because that is where contradictions hide:

- Does every entity in the business logic appear somewhere in the data model?
- Does every screen have the data it displays available from the API?
- Does every business rule have a named enforcement point and a test?
- Does every permission in phase 02 appear in the authorisation design?
- Does the stack actually support what the architecture assumes?
- Does every technology in the stack have rules installed?
- Does the plan's first task actually run without the later ones?
- Is anything in the plan not traceable back to a requirement? Why is it there?
- Is any requirement missing from the plan entirely?

## Then check the artifacts exist

For the phases your triage class requires, confirm the output file exists and
is not a stub. A file containing "TBD" is a missing file.

## Placeholder scan

Search the artifacts for `TBD`, `TODO`, `???`, `[fill in]`. Every one is
either resolved now or explicitly listed as an open question with an owner.

## Classify what is still unknown

Three buckets, and they are treated differently:

- **Blockers** - proceeding without an answer risks building the wrong thing.
  Stop and ask. This is true even in autonomous mode.
- **Important, non-blocking** - proceed, but state the assumption prominently
  and flag where it would be expensive to reverse.
- **Minor** - pick a sensible default, record it, move on.

## The safety pre-flight

Before the first line of implementation:

- Is there anything in the plan that touches production-like data? If so, the
  backup gate in `../core/SAFETY.md` applies.
- Are credentials needed that you do not have? Say so now, not at deployment.
- Is anything in the plan irreversible? Name it explicitly.

## Present it

Summarise for the human in a few paragraphs: what will be built, in what
order, the key decisions and their rationale, the assumptions being made, and
the open questions.

Then **stop and wait for approval.** Presenting the gate and starting
implementation in the same message is not a gate.

## Output

`.agent-toolkit/reports/11-gate.md` - the coherence findings, the open
questions by class, and the go / no-go recommendation.
