---
name: using-superpowers
description: Use when starting a development task - establishes how to find and use relevant skills before action.
---

# Using Superpowers

If a relevant project-local skill exists, read it before acting. Process skills define *how* to work; technology skills define *how* to implement.

## Priority

1. Direct human instructions and project rules (`AGENTS.md`, `.agent-toolkit/CORE.md`)
2. Relevant process skills
3. Relevant technology/domain skills
4. General model defaults

The selected project interaction mode explicitly controls how often to ask questions:
- Thorough: ask materially useful questions.
- Focused: ask important/blocking questions only.
- Autonomous: decide reversible/non-critical ambiguity independently; stop only for true blockers or high-impact actions.

## Core routing

- New project / major feature → discovery + planning workflow first.
- Bug / failing test → systematic debugging before proposing fixes.
- Feature/refactor → test-driven implementation when practical.
- Written plan → execute task-by-task with verification checkpoints.
- Before completion → verification-before-completion.
- Before commit → atomic Git rules.

Do not load every skill just because it is installed. Load only skills relevant to the current task.
