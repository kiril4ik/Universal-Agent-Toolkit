# 08 - Architecture

How the system is put together. Skip for task-class work.

## Prefer the simplest thing that meets the requirement

The requirement includes real scale, real team size and real operational
constraints - not imagined future ones. A monolith that a small team can
deploy on a Friday beats a microservice architecture that nobody can debug.

Every boundary you add is a boundary someone maintains, monitors and debugs
across. Add them when something forces you to, and write down what forced it.

## Define

**Modules and boundaries.** What the parts are, what each is responsible for,
and what it explicitly is not. For each module, someone should be able to
answer: what does it do, how do you use it, and what does it depend on -
without reading its internals.

**Data model.** Tables, keys, indexes, constraints. Where the invariants from
phase 02 are enforced - database constraint, application validation, or both.
Prefer the database for anything that must always be true.

**API surface.** Endpoints or operations, their shapes, versioning strategy,
error format. Pick one error format and use it everywhere.

**Authentication and authorisation.** How identity is established, how it is
carried, where permission is checked. Permission checks belong in one place,
not scattered across controllers.

**Background work.** What runs asynchronously, what triggers it, what happens
when it fails, and whether it is safe to run twice. Assume it will run twice.

**External integrations.** For each: what it does, timeout, retry policy, what
happens when it is down, and whether failure is user-visible.

**Errors and logging.** How errors propagate, what gets logged, what gets
alerted. Log enough to debug, never enough to leak credentials or personal data.

## Where the invariants live

Take the rules from phase 02 and, for each, name the code that enforces it and
the test that proves it. A business rule with no enforcement point is a bug
waiting to be filed.

## Design for testability

If a unit is hard to test, the boundary is wrong. Push side effects to the
edges and keep the domain logic pure enough to test without infrastructure.

## Output

`docs/architecture.md` - modules, data model, API surface, auth model,
background work, integrations, error handling, and the invariant-to-
enforcement map.

Plus `.agent-toolkit/reports/08-architecture.md`.
