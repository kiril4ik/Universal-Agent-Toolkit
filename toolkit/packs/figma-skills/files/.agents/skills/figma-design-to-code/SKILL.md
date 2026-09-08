---
name: figma-design-to-code
description: "Mandatory workflow for implementing a Figma design as code. Use before calling Figma design-context tools or translating a Figma node into code."
---

# Implement a Figma Design as Code

Use this skill for design → code. Pull design context from Figma first, then adapt it into the project's real stack.

## Workflow

1. Call Figma design-context tooling for the target node before writing code.
2. Treat generated/reference code as **reference**, not production code to paste verbatim.
3. Inspect the target project for existing components, layout patterns, tokens, and design-system primitives. Reuse them.
4. Apply design evidence by priority:
   - Code Connect / mapped codebase components
   - component documentation
   - design annotations
   - design tokens
   - raw styling/absolute geometry
5. Reproduce images/icons faithfully. Prefer exported assets or an existing project icon whose glyph genuinely matches.
6. Verify the implementation visually and behaviorally with Playwright/browser tooling.
7. Check responsive states, empty/error/loading states, focus/keyboard behavior, and console/network errors.

If the target URL/file does not identify a specific node and the agent cannot reliably determine it, ask for a node-specific target rather than guessing.

**Source:** Figma `mcp-server-guide`, pinned in `vendor/SOURCES.md`.
