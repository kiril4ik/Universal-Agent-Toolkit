# Documentation

Start with [Getting started](GETTING-STARTED.md). Everything else is
reference, and each page answers one question.

## By question

| Question | Page |
|---|---|
| How do I install it into my project? | [Getting started](GETTING-STARTED.md) |
| What does every command and flag do? | [CLI reference](CLI.md) |
| Does it support my coding agent? What does that agent get? | [Agent support](AGENT-SUPPORT.md) |
| What can be installed, and how is it chosen? | [Packs & profiles](PACKS.md) |
| How does the planning workflow run? | [Planning workflow](WORKFLOW.md) |
| What rules apply to every project, always? | [Core policy](CORE-POLICY.md) |
| Where does vendored content come from, and how is it trusted? | [Vendoring & provenance](VENDORING.md) |
| How do I ship the app to a server? | [Deployment](DEPLOYMENT.md) |
| The agent is ignoring the rules. Now what? | [Troubleshooting](TROUBLESHOOTING.md) |
| Why is it built this way? | [Architecture](ARCHITECTURE.md) |

## By role

**I want to configure a project.**
[Getting started](GETTING-STARTED.md) → [Packs & profiles](PACKS.md) →
[CLI reference](CLI.md)

**I want my agent to actually follow the rules.**
[Core policy](CORE-POLICY.md) → [Planning workflow](WORKFLOW.md) →
[Troubleshooting](TROUBLESHOOTING.md)

**I want to extend the toolkit itself.**
[Architecture](ARCHITECTURE.md) → [Packs & profiles](PACKS.md#writing-a-pack)
→ [Agent support](AGENT-SUPPORT.md#adding-an-agent) →
[Vendoring & provenance](VENDORING.md)

**I am deploying.**
[Deployment](DEPLOYMENT.md) → [Core policy](CORE-POLICY.md#safety)

## Conventions in these pages

- `uat` means `./bin/uat` from a toolkit checkout, or
  `.agent-toolkit/toolkit/uat` in an embedded project.
- Counts (62 packs, 14 agents, 166 tests) are what the current tree reports.
  Confirm with `uat catalog`, `uat agents` and `./bin/uat-test`; those are the
  authority, not this prose.
- Anything under `vendor/` is a verbatim upstream snapshot and is never
  edited. See [Vendoring & provenance](VENDORING.md).
