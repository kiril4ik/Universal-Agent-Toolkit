# 08 - Design

Produce the visual design the implementation will follow. Skip when there is
no user interface.

**This phase runs after stack (04) and architecture (06), deliberately.** You
are designing against a chosen component library and a data model that can
actually serve the screens. Check both before you start:

- `docs/stack.md` - the CSS approach and component library you must build on
- `docs/architecture.md` - what data each screen can actually be given
- `docs/screens.md` - the screens, their five states, and their permissions

If the design you want needs data the architecture does not provide, raise it
now. Changing the data model here is cheap; changing it after the design is
implemented is not.

There are two paths. Decide which one applies before starting, and say so.

## Path A - a design already exists (Figma-first)

**This is the preferred path when a designer is involved.** An existing design
system always outranks anything an agent generates.

### Setup

The `figma-design` pack installs the MCP configuration and the integration
guide. It requires things this toolkit cannot provide for you:

- the Figma desktop app, running
- a Figma seat that permits Dev Mode / MCP access
- the MCP server enabled in Figma's preferences

`.agent-toolkit/mcp/README.md` lists exactly what is missing. If the
prerequisites are not met, say so and fall back to Path B rather than
guessing at the design.

### Implementing faithfully

The point of this path is fidelity. Therefore:

- **Pull values, do not eyeball them.** Read spacing, colour, radius, weight
  and size from the file. A screenshot is a last resort, and you should say
  when you are working from one.
- **Map to tokens, not literals.** If the design has a colour style, it
  becomes a token. Hard-coded hex values in components are how design systems
  rot.
- **Match the component structure** the designer used. If they built a
  variant set, build variants, not five near-copies.
- **Do not silently improve the design.** If something is inconsistent, has an
  accessibility problem, or is missing a state, raise it. Then implement what
  was decided, not what you preferred.
- **Ask for the states.** Designs usually show the full state. You need empty,
  loading, error and disabled too - see `03-screens-and-flows.md`.

### Verify against the source

Implement, screenshot, compare against the design, fix the differences. State
what you compared and what still differs. "Looks about right" is not
verification.

## Path B - no design exists (generate it)

When there is no designer, generate a coherent design rather than improvising
per screen.

### Establish direction first

Before any screen: the product's character in a few words, and the
constraints - existing brand, industry conventions, accessibility targets,
platforms.

If a `ui-ux-pro-max` or equivalent design skill is installed, use it. It
carries style catalogues, palettes and font pairings that beat inventing from
scratch.

### Then the system, then the screens

Define tokens before components and components before pages:

- **Colour** - background, surface, text, muted text, border, primary, and
  semantic success / warning / danger. Both light and dark if you support
  both. Check contrast: 4.5:1 for body text, 3:1 for large text and UI
  boundaries.
- **Type** - family, the size scale, weights, line heights.
- **Space** - one scale, used consistently. Not arbitrary pixel values.
- **Radius, borders, shadows, motion durations.**

Then the components, each with all its interaction states: default, hover,
focus-visible, active, disabled, error, loading.

Only then compose screens. A screen assembled from a real system is
consistent by construction.

### Accessibility is not a later pass

Visible focus on every interactive element. Colour is never the only carrier
of meaning. Touch targets large enough to hit. Motion that respects
`prefers-reduced-motion`.

## Output

`docs/design/` - direction, tokens (in a machine-readable form the code can
import), component specifications, and screen designs or references.

Plus `.agent-toolkit/reports/08-design.md`, stating which path was used and,
for Path A, what could not be pulled from the source.
