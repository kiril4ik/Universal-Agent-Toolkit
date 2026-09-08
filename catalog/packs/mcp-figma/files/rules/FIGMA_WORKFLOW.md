# Figma design-to-code

How to implement a Figma design faithfully. Written by this toolkit - see
the note at the end about Figma's own skills, which are **not** bundled here.

## Before you start

Confirm the MCP connection works (`.agent-toolkit/mcp/README.md` lists the
prerequisites). If it does not, say so and switch to the generate-a-design
path in `../workflow/05-design.md`. Do not implement from a screenshot while
implying you worked from the source.

## Pull values, never estimate them

The entire point of connecting to Figma is that you stop guessing.

| Do | Do not |
|---|---|
| Read the spacing value from the node | Eyeball "that looks like 16px" |
| Read the colour style / variable | Sample a pixel from a screenshot |
| Read the text style (size, weight, line height) | Assume it is the default |
| Read the corner radius, border, shadow | Approximate from the render |
| Read the component's variant structure | Rebuild it as separate components |

If a value cannot be read, say which one and that you estimated it.

## Map to tokens, not literals

A design system's value dies the moment values are hard-coded.

- A Figma **colour style or variable** becomes a design token in code.
- A Figma **text style** becomes a typography token or a utility class.
- Figma **spacing variables** map onto your spacing scale.

If the design uses a raw value with no style attached, that is worth raising -
it is usually an oversight in the design, and hard-coding it propagates the
problem into the codebase.

## Match structure, not just appearance

Look at how the designer built it:

- A **component set with variants** becomes one component with props, not
  five similar components.
- **Auto-layout** maps to flex/grid. Direction, gap, padding, alignment and
  the hug/fill behaviour all translate directly - read them rather than
  reverse-engineering the visual result.
- **Constraints** describe resize behaviour, which tells you what the
  responsive intent was.

## The states designs usually omit

A Figma file typically shows the populated, happy-path state. You still need
the rest, from `../workflow/03-screens-and-flows.md`: empty, loading, partial,
error. Plus interaction states: hover, focus-visible, active, disabled.

Ask for them. If nobody answers, design them consistently with the system and
list what you invented in your report.

## Raise problems, then build what was decided

If you find an accessibility failure (contrast below 4.5:1 for body text, a
touch target that is too small, meaning carried by colour alone), an
inconsistency, or a missing state - **say so before implementing**.

Then implement what was decided, not what you would have preferred. Silently
"fixing" a designer's work is how trust between design and engineering breaks.

## Verify against the source

Implement, screenshot the result (the Playwright MCP does this), compare
against the design, and list what still differs and why. State the comparison
explicitly. "Matches the design" without a comparison is not verification -
see `../core/VERIFICATION.md`.

## Figma's own skills are not bundled

Figma publishes a set of skills (`figma-design-to-code`, `figma-generate-design`
and others) in `github.com/figma/mcp-server-guide`. They are **deliberately not
vendored into this toolkit**: they are governed by the Figma Developer Terms
rather than an open-source licence, so redistributing them here would not be
appropriate.

They are good, and you should use them. Install them into your own project
directly from source:

```bash
git clone --depth 1 https://github.com/figma/mcp-server-guide /tmp/figma-guide
cp -r /tmp/figma-guide/skills/figma-design-to-code .agent-toolkit/skills/
```

By using the Figma MCP server and its resources you accept the Figma
Developer Terms.
