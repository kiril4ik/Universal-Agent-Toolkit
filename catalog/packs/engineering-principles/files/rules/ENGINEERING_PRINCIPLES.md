# Engineering principles

The vocabulary every codebase is judged by. Short on purpose: these are
reminders, not a textbook.

**Read `PRINCIPLES_PRECEDENCE` at the bottom before applying any of it.** These
principles describe where a design should end up. They are not a licence to
build that design before the code needs it.

## SOLID

| | Principle | In practice |
|---|---|---|
| **S** | Single responsibility | A module has one reason to change. If describing it needs "and", look again. |
| **O** | Open/closed | Adding a case should not mean editing every existing case. |
| **L** | Liskov substitution | A subtype must work anywhere its base type does - no stronger preconditions, no weaker guarantees. |
| **I** | Interface segregation | Many small interfaces beat one broad one. Callers should not depend on methods they never call. |
| **D** | Dependency inversion | Depend on an abstraction you own, not on a concrete detail you do not. |

SOLID is object-oriented in origin. In a codebase built from functions and
modules the same ideas hold - one job per function, extend by adding rather
than editing, depend on a signature rather than an implementation.

## DRY - and its opposite failure

Don't Repeat Yourself is about **knowledge**, not characters. Two pieces of
code that look alike but change for different reasons are not duplication,
and merging them couples two things that wanted to move apart.

> Duplication is far cheaper than the wrong abstraction.

The practical rule: duplicate freely on the first and second occurrence.
Extract on the third, when you can see what actually varies.

What DRY does mean, always: one source of truth for a value, a schema, a
validation rule, or a business fact. A constant defined twice is a bug
waiting for someone to change one of them.

## KISS and YAGNI

The simplest thing that fully solves the problem. No configurability nobody
asked for, no extension points for futures nobody has described, no error
handling for states that cannot occur.

Both are covered in depth by the `karpathy-guidelines` skill, which is
installed alongside this file. It is the operative version; this section
exists so the vocabulary is in one place.

## Composition over inheritance

Inheritance couples a subclass to its parent's internals forever. Composition
lets you swap a behaviour without touching what uses it. Reach for
inheritance when the relationship is genuinely "is a kind of" and stable;
otherwise pass the behaviour in.

Deep hierarchies are a smell. Three levels is usually two too many.

## Names, comments and structure

Two rule files installed with this pack cover these properly:

- `CLEAN_CODE.md` - naming, function size, encapsulation, structure
- `CODE_COMMENTS.md` - comment the *why*, never the *what*

The one-line version: if a function needs a comment to say what it does, its
name is wrong or it does too much.

## Design patterns

A pattern is a name for a solution you already needed. Recognising one after
the fact is useful; reaching for one before the problem exists is
over-engineering with a respectable vocabulary.

For the catalogue and when each pattern earns its place:

```bash
uat install --project . --agent <your-agent> --add design-patterns
```

That pack is deliberately not installed by default - see below.

## PRINCIPLES_PRECEDENCE

These principles conflict with the simplicity rules in `karpathy-guidelines`
if read as instructions to follow immediately. They are not. **When the two
disagree, simplicity wins and the principle waits.**

| Tempting reading | What to do instead |
|---|---|
| "Depend on abstractions - so define an interface now." | One implementation needs no interface. Add it when the second arrives. |
| "Open/closed - so make it extensible now." | Extensible for a extension nobody has described is speculation. Wait for the second case. |
| "DRY - these three lines repeat." | Three similar lines beat a premature abstraction. Extract on the third *real* occurrence. |
| "SRP - this class is too big, split it." | Not while you are here for something else. Note it; do not refactor what you were not asked to touch. |

The two optional packs below go further than this file and are **not**
installed by default, because applied unconditionally they would fight the
simplicity rules:

- `design-patterns` - the GoF catalogue. Its "generate the interface first"
  guidance is right when you have two implementations and wrong when you have
  one.
- `object-calisthenics` - nine hard constraints (wrap every primitive, two
  fields per class, no `else`). A sharp tool for a domain model built that way
  from the start; disruptive applied to an existing codebase that was not.

Install either deliberately, for a project whose team has agreed to it.
