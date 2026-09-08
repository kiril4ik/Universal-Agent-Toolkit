---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code.
---

# Writing Plans

Write a comprehensive implementation plan that a competent engineer/agent can execute without hidden context.

## Plan rules

- Map exact files/modules before tasks.
- Break work into independently testable, reviewable units.
- Each task states goal, dependencies, files, interfaces, implementation steps, tests, acceptance criteria, and verification commands.
- Prefer vertical slices when practical.
- Use TDD/red-green-refactor for behavior changes when appropriate.
- No placeholders such as "TODO", "add error handling", or "write tests".
- Keep tasks small enough to verify and commit coherently.
- Include a `Spec:` pointer and global constraints.
- End with a self-review: spec coverage, placeholder scan, interface/type consistency, migration/data-safety review.

Save plans under `docs/plans/` or the project’s established planning location.
