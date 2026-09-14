# Codex image generation

Use this capability only when `.agent-toolkit/project.json` sets
`"image_generation"` to `"ask"` or `"auto"` and a bitmap asset would improve
the product. Do not use it for existing SVG systems, simple CSS decoration, or
when the policy is `"off"`.

## Capability gate

Before relying on Codex, verify both availability and responsiveness:

```bash
command -v codex
codex --version
codex exec 'Reply with exactly READY.'
```

If any check fails, report that image generation is unavailable and continue
with an existing asset or a code-native alternative. Do not pretend an image
was generated.

With `"ask"`, describe the proposed assets and obtain approval before invoking
the CLI. With `"auto"`, generate them when the requirement clearly benefits
from original imagery.

## Generation

Use an explicit prompt, destination, dimensions or aspect ratio, visual style,
content constraints, and the project path. For example:

```bash
codex exec 'Use $imagegen to generate a photorealistic garden tomato growing naturally on the vine, suitable as a hero image for a tomato growing guide. No text. Save it as public/images/plants/tomato.jpg.'
```

- Never overwrite a user-owned asset unless the task explicitly authorizes it.
- Do not put secrets, private data, real people, or protected brand assets into
  a prompt.
- Inspect the resulting file at its actual resolution. Check composition,
  cropping, text artifacts, accessibility implications, and fit with the design
  system before using it.
- Treat generated assets as implementation inputs, not proof that a page works.
  Browser acceptance and responsive screenshots are still required.
