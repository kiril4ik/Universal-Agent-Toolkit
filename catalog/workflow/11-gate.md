# 11 - Gate

The approval before implementation starts.

<EXTREMELY-IMPORTANT>
**The approval is never skipped, at any class.** Nothing is implemented until
a human has seen what you intend and said yes.

**The review that precedes it scales with the class.** A one-line fix does not
get a cross-artifact coherence audit - there are no artifacts to cross-check.
Running the heavy version on small work is its own failure: it teaches people
to wave the gate through, which is how the gate stops working.
</EXTREMELY-IMPORTANT>

## What the gate is, per class

| Class | What you present | Report? |
|---|---|---|
| **Task** | the short design from `brainstorming`'s bounded path: approach, files you will touch, how you will test it. A few sentences. | no |
| **Feature** | the plan, plus the coherence checks below over the artifacts that exist | yes |
| **Product** | everything below | yes |

For Task class this **is** `brainstorming`'s approval gate - the same single
stop, not a second one. See "Precedence" in `README.md`.

The rest of this file describes the Feature and Product version.

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
implementation in the same message is not a gate. This applies at every class,
including Task - a two-sentence design still needs a yes before you type code.

## Red flags

| Thought | Reality |
|---|---|
| "It's a Task, so there's no gate" | The review scales. The approval does not. |
| "We discussed it, that counts as approval" | Discussion is not approval. Ask for the yes. |
| "I'll present the plan and start on the obvious part" | That is skipping the gate while describing it. |
| "The full checklist is overkill here" | Then you classified it as Task - use the Task row and move on. |
| "They approved the design, so I can also do the refactor" | Approval covers what you presented. Nothing else. |

## Output

For Feature and Product: `.agent-toolkit/reports/11-gate.md` - the coherence
findings, the open questions by class, and the go / no-go recommendation.

For Task: no file. The approval happens in the conversation, and phase 12
records what was built.
