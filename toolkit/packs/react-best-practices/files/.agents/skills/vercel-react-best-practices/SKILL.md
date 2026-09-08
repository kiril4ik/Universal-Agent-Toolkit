---
name: vercel-react-best-practices
description: React and Next.js performance optimization guidelines. Use when writing, reviewing, or refactoring React/Next.js code.
---

# React / Next.js Best Practices

Prioritize:

1. **Eliminate waterfalls** — start independent async work early; await together; use streaming/Suspense deliberately.
2. **Bundle size** — prefer direct imports, code-split genuinely heavy client code, defer non-critical third parties.
3. **Server performance** — authenticate server actions, avoid shared mutable request state, minimize client serialization, deduplicate appropriate work.
4. **Client data** — deduplicate requests/listeners and keep persistent client storage versioned/minimal.
5. **Re-renders** — derive state during render, use functional state updates, avoid unnecessary effects/memoization, do not define components inside components.
6. **Rendering** — use content visibility/virtualization for genuinely large lists; preserve hydration correctness.
7. **JavaScript hot paths** — use Maps/Sets for repeated lookups, avoid repeated iterations where meaningful, cache only proven expensive work.
8. **Advanced patterns** — use stable event/ref patterns when they solve a real problem, not by default.

Always follow the installed React/Next.js version and current project conventions.

**Source:** Vercel `agent-skills`, pinned in `vendor/SOURCES.md`.
