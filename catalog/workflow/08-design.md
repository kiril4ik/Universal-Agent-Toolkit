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

**On Claude Code, prefer Claude Design for whichever path you are on.** See
"Claude Code: use Claude Design" below before you start — on Path A it
receives the imported design, and on Path B it is how you generate one.

## Path A - a design already exists (Figma-first)

**This is the preferred path when a designer is involved.** An existing design
system always outranks anything an agent generates.

### Setup

The `mcp-figma` pack installs the MCP configuration and the integration
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

## Claude Code: use Claude Design

When the agent is Claude Code, Claude Design is the preferred surface for this
phase. It keeps the design as a real, revisable artifact rather than prose
describing one, and it hands off to implementation without going through a
screenshot.

Check whether it is connected before you start:

```bash
claude mcp list          # is `claude-design` there?
```

If it is not, install the pack and follow what it tells you:

```bash
uat install --project . --agent claude-code --add mcp-claude-design
```

`.agent-toolkit/mcp/README.md` then carries the exact steps. In short:

```bash
claude mcp add --scope user --transport http claude-design https://api.anthropic.com/v1/design/mcp
```

then, in Claude Code, `/design-login` once, and `/design-sync` to pull this
project's design system in.

**User scope, not project scope, is deliberate.** Claude Design is tied to an
individual Anthropic account and a paid plan. Putting it in a committed
`.mcp.json` gives every teammate an entry that will not work until they
personally sign in, and that some of them may not be entitled to use at all.

### Prerequisites this toolkit cannot satisfy

A paid plan (Pro, Max, Team or Enterprise), and Claude Design is in beta. If
the plan does not include it, **say so and fall back** to the ordinary path
below — do not describe designs you could not actually produce.

Other agents cannot use this server: `/design-login` and `/design-sync` are
Claude Code commands. On any other agent, skip this section entirely.

### How it changes each path

- **Path A (Figma exists)** — Figma still owns the source of truth. Use
  `/design-sync` so what you generate starts from the real components rather
  than from scratch, and keep pulling values from Figma.
- **Path B (no design exists)** — generate in Claude Design instead of
  improvising screen by screen. Establish direction, then tokens, then
  components, then screens, exactly as below; Claude Design is the surface,
  not a replacement for the order.

The rules below still apply in full. Claude Design does not exempt you from
the contrast checks, the five states per screen, or the accessibility
requirements — it makes them easier to see, which is the point.

## Output

`docs/design/` - direction, tokens (in a machine-readable form the code can
import), component specifications, and screen designs or references.

Plus `.agent-toolkit/reports/08-design.md`, stating which path was used and,
for Path A, what could not be pulled from the source. When Claude Design was
used, link the designs; when it was unavailable, say why.
