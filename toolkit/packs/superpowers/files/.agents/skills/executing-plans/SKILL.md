---
name: executing-plans
description: Use when a written implementation plan exists and should be executed task-by-task with review checkpoints.
---

# Executing Plans

1. Read the plan and referenced spec.
2. Review the plan for contradictions or dangerous assumptions.
3. Work in an isolated branch/worktree when appropriate; never start substantial implementation on main/master without explicit consent.
4. Execute tasks in order, maintaining a progress ledger.
5. For each task: implement, verify, review, then commit one coherent change set.
6. In Autonomous mode, make reversible rulings and record assumptions instead of repeatedly stopping.
7. Stop for destructive/irreversible operations, security-sensitive actions, external publish/push/merge actions that require approval, or a truly broken plan.
8. Finish with full verification and a broad diff/review against the spec.
