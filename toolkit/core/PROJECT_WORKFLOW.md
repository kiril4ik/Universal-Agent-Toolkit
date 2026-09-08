# Per-Project Planning Workflow

This workflow starts **after** the universal toolkit exists and selected resources have been copied into the project.

## Step 0 — choose interaction mode

Ask first:

1. **Thorough** — ask all materially useful questions.
2. **Focused** — ask only important/blocking questions and use reasonable defaults elsewhere. Default.
3. **Autonomous** — make reasonable decisions independently and ask only when a wrong assumption would materially change the product, or before destructive/irreversible actions.

Record the choice in `.agent-toolkit/project.json`.

The selected mode affects question frequency, not safety. Database deletion, credential changes, production deployment, irreversible migrations, and other high-impact actions still require safeguards/approval.

## Step 1 — repository discovery

Inspect files, documentation, current rules/skills/MCP, package manifests, Docker, CI/CD, deployment, tests, code style, and existing architecture. Determine whether this is a new project or work on an existing codebase.

Report: checked, found, decisions, files changed, assumptions, open questions, next step.

## Step 2 — local toolkit audit

Check what is already installed. Do **not** reinstall or overwrite existing skills/rules/MCP configuration. Select additional stack-specific packs only when repository evidence requires them.

## Step 3 — product discovery before questions

Infer as much as possible first: product purpose, users, use cases, entities, workflows, pages, integrations, constraints, current UI, infrastructure.

Separate facts, assumptions, and unknowns.

## Step 4 — clarification

Ask according to the selected interaction mode. Never ask what can be answered from repository evidence.

Prioritize business goals, MVP scope, roles/permissions, critical workflows, required integrations, compliance/security, deployment constraints, expected scale, and design/brand constraints.

## Step 5 — business logic

Document users, roles, permissions, entities, relationships, workflows, state transitions, validation, edge cases, failures, external integrations, confirmed requirements, assumptions, and out-of-scope ideas.

## Step 6 — pages and user flows

For every page/screen define purpose, target user, displayed data, actions, forms/validation, loading/error/empty states, permissions, responsive behavior, and navigation. Create sitemap/route map when useful.

## Step 7 — content

Generate realistic product copy and representative demo data. Avoid lorem ipsum when meaningful content is possible.

## Step 8 — design

For UI projects use the selected design packs and Figma tooling. Establish design direction, hierarchy, typography, spacing, components, colors, states, responsiveness, and tokens. Existing Figma/design-system sources outrank generated approximations.

## Step 9 — technology stack

Choose technologies based on actual constraints, not familiarity alone. Document rationale for backend, frontend, DB, cache, queue, search, storage, auth, UI/CSS, tests, analysis/linting, Docker, web server, CI/CD, and observability.

## Step 10 — stack rules

Ensure local rules exist for every significant selected technology. Add only missing relevant packs. Do not load unrelated rules into context.

## Step 11 — architecture

Document modules/boundaries, data model, APIs, auth/authz, background jobs, integrations, caching, storage, errors/logging, security boundaries, retry/idempotency/rate-limit/observability/scaling when relevant. Prefer the simplest architecture that satisfies requirements.

## Step 12 — engineering standards

Define naming, dependencies, validation, migrations, testing, static analysis, formatting, documentation, Git/PR workflow, and security. Automate enforcement where practical.

## Step 13 — local Docker

Prefer reproducible local startup. Persistent databases must use named volumes and rebuilds must preserve data. Setup scripts may initialize an empty DB but may not wipe an existing one.

## Step 14 — deployment: clean Ubuntu

Provide a repeatable fresh-server path: packages/container runtime, firewall, directories, reverse proxy, TLS, app config, DB/cache/queue/scheduler, migrations, permissions, health checks, and logging.

## Step 15 — deployment: existing server

Detect existing ports/services/config first. Avoid destructive changes. Back up relevant configuration and databases before risky modifications. Prefer idempotent changes.

## Step 16 — implementation plan

Break work into independently verifiable tasks. Each task states goal, dependencies, exact files/modules, implementation work, tests, acceptance criteria, and verification commands. Prefer incremental vertical slices.

## Step 17 — verification strategy

Define unit/integration/API/E2E tests, linting, formatting, static analysis, builds, security checks, migration checks, Docker health checks as applicable.

## Step 18 — final pre-implementation review

Verify requirements, business logic, pages, content, design, architecture, stack, rules, skills, MCP, Docker, deployment, tests, and implementation plan are coherent and present locally.

## Step 19 — remaining questions

Separate blockers, important non-blockers, and assumptions. In Autonomous mode, proceed on non-blockers with documented defaults.

## Reporting

Every major step writes a concise report to `.agent-toolkit/reports/NN-step-name.md`:

```markdown
# Step N — Name

## What was checked
## What was found
## Decisions made
## Files added/changed
## Skills/rules/MCP used
## Assumptions
## Open questions
## Next step
```
