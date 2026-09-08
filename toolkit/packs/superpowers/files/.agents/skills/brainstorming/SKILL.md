---
name: brainstorming
description: Use before new features, components, behavior changes, or architectural work to understand intent and design before implementation.
---

# Brainstorming / Discovery

Follow `.agent-toolkit/CORE.md` and the selected interaction mode.

## First classify scope

- **Spike** — feasibility/probe. Output is a recommendation, not production code.
- **Bounded** — well-scoped change to an existing flow.
- **Architectural** — new project/subsystem or change affecting major boundaries/interfaces.

## Process

1. Explore repository/context before asking questions.
2. Separate facts, assumptions, and unknowns.
3. Ask questions according to the selected interaction mode:
   - Thorough: cover all material product/architecture/design constraints.
   - Focused: ask only important/blocking questions.
   - Autonomous: use reasonable defaults and document them; ask only if a wrong assumption changes the product materially.
4. For architectural work, propose 2–3 approaches with trade-offs when alternatives are real.
5. Present a coherent design/spec before implementation.
6. For UI work, use Figma/UI skills and visual verification where available.
7. Transition to the planning skill.

## Scope discipline

Prefer the simplest design that meets the real requirement. Avoid speculative flexibility, unrelated refactoring, and premature microservices.
