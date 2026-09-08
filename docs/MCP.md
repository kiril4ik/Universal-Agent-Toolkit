# MCP Strategy

## Core

### Playwright MCP

Browser navigation, UI verification, E2E workflows, screenshots/accessibility checks, and behavior validation. Selected by default because agents need to see and exercise the UI they build.

### Context7

Version-aware library/framework documentation. Selected by default for code projects; use it when APIs, framework versions, or current library guidance matter.

## Frontend/design

### Figma remote MCP

Use the official remote Figma endpoint when the project has UI/design work. Pair it with Figma skills and design-to-code workflow rather than treating generated reference code as production code.

## Optional authenticated integrations

- GitHub MCP — repository/issues/PR workflows when native GitHub access is insufficient.
- Sentry MCP — production error/trace investigation for projects that use Sentry.

## Intentionally not core

- Filesystem MCP: most coding agents already have filesystem tools; redundant broad filesystem servers add risk.
- Generic database-write MCP: dangerous by default. Prefer app/DB CLI with explicit credentials, environment, backup, and read-only inspection when possible.
- Memory MCP: project documentation and Git are preferable for durable engineering state unless there is a concrete need.

## Local runtime policy

Supported stdio runtimes are installed under:

```text
<project>/.agent-toolkit/runtime/
```

Never globally. Exact versions are pinned and checked before installation.

Remote MCPs such as Figma do not have a local server package to vendor; this repository stores endpoint configuration and local skills/instructions.
