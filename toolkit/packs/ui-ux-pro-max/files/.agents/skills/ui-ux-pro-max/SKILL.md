---
name: ui-ux-pro-max
description: UI/UX design intelligence for web, mobile, and desktop. Use when designing, building, reviewing, or fixing interfaces.
---

# UI/UX Pro Max — Local Compatibility Pack

This project-local pack follows the UI UX Pro Max workflow while remaining usable without a globally installed CLI.

## Priority

1. Accessibility
2. Touch and interaction
3. Performance / layout stability
4. Product-appropriate style selection
5. Responsive layout
6. Typography and color
7. Motion
8. Forms and feedback
9. Navigation
10. Charts/data visualization

## New project/page workflow

1. Analyze product type, users, usage context, brand/style constraints, and detected frontend stack.
2. Establish a **design system before markup**:
   - visual direction and anti-patterns
   - semantic color tokens
   - typography scale
   - spacing/radius/elevation
   - layout/container rules
   - component states
   - responsive behavior
3. Use realistic product content.
4. If Figma exists, treat Figma/design-system sources as visual truth.
5. If no design exists, create one using Figma/design tooling when available.
6. Implement with the project's actual components/tokens rather than generated generic components.
7. Validate in the browser with Playwright at relevant viewport sizes.

## Quality guardrails

- Avoid generic "AI SaaS" appearance when the product calls for a distinct identity.
- Do not use emoji as interface icons when a consistent icon system exists.
- Do not mix unrelated visual styles.
- Body text should remain readable; contrast/focus/keyboard states are functional requirements.
- Touch targets must be comfortably usable.
- Do not animate layout-heavy properties unnecessarily; support reduced motion.
- Design empty/loading/error/success/disabled states, not only the happy path.
- Avoid raw arbitrary color/spacing values once design tokens exist.
- Mobile/responsive behavior is part of the design, not a post-processing step.

## Existing products

Preserve existing product behavior and established design-system conventions. Improve only what serves the requested goal. Reuse components before inventing duplicates.

**Upstream:** `nextlevelbuilder/ui-ux-pro-max-skill` v2.15.0. The upstream full searchable dataset is tracked in `vendor/SOURCES.md`; this compatibility pack contains the reliable workflow/guardrails needed by project agents without requiring a global CLI.
