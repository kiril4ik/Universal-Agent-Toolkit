# Packs & profiles

A **pack** is the unit of installation: one small JSON file saying what to
install, what to call it, and when it applies. A **profile** is a named
bundle of packs.

```bash
uat catalog                    # 61 packs, 6 profiles
uat catalog --search wordpress # search all ~450 vendored rule documents
uat catalog --unmapped         # vendored content no pack exposes
```

## Tiers

| Tier | Count | When it installs |
|---|---|---|
| `core` | 3 | always, in every install |
| `recommended` | 8 | when the detected stack asks for it |
| `optional` | 50 | when you ask for it, or a profile includes it |

**Core** is `superpowers` (engineering-discipline skills), `security` (OWASP
rules) and `karpathy-guidelines` (anti-overcomplication guardrails). Those
apply to any codebase in any language, which is the bar for core.

> A bare `uat install --agent <id> --yes` on a project with no detectable
> stack installs the core tier only — three packs. That is the floor, not a
> setup. Pick a profile or use the interactive list for real work.

## How packs get selected

Four inputs, checked in this order:

1. `--all` — everything.
2. `--packs a b c` — exactly these, plus whatever they `require`.
3. `--profile nextjs` — the profile's packs, plus its parents, plus requires.
4. Nothing — **detection**. Core packs always; a pack whose `detect` tokens
   intersect the detected stack is added.

On a terminal, when you gave none of the first three, the result is
pre-checked in an interactive toggle list rather than installed blind.

`--add a b` is additive on top of any of the four.

### Detection

`uat detect` reads manifests, lockfiles and marker paths — `package.json`,
`tsconfig.json`, `composer.json`, `pyproject.toml`, `requirements.txt`,
`manage.py`, `go.mod`, `Cargo.toml`, `*.csproj`, `pom.xml`, `build.gradle`,
`Gemfile`, `Dockerfile`, `compose.yml`, `*.tf`, `k8s/`, `helm/`,
`.github/workflows/` — and prints the evidence for every token:

```
  node                         package.json
  react                        package.json requires react
  nextjs                       package.json requires next
  typescript                   tsconfig.json
  pnpm                         pnpm-lock.yaml
```

It never executes project code. A Laravel + React + PostgreSQL project gets
PHP, Laravel, React, TypeScript, PostgreSQL and Docker rules — and no
Symfony, Vue, MySQL or Flutter rules polluting the agent's context.

## Profiles

| Profile | Packs | For |
|---|---|---|
| `core` | 5 | the floor plus safety essentials |
| `frontend` | 10 | any browser UI |
| `nextjs` | 18 | Next.js + React + Tailwind + TypeScript |
| `laravel-react` | 19 | Laravel API with a React front end |
| `python-api` | 12 | FastAPI / Django services |
| `design` | 13 | UI/UX, design systems, Figma, visual verification |

Profiles compose with `extends`, so `nextjs` inherits everything in
`frontend` and adds to it. Nothing is duplicated between them.

```bash
uat install --project ~/app --agent claude-code --profile nextjs
```

## What a pack can install

| Kind | Where it lands | Example |
|---|---|---|
| rules | `.agent-toolkit/rules/GO.md` | `go`, `laravel`, `postgresql` |
| skills | `.agent-toolkit/skills/<name>/` | `superpowers`, `ui-ux-pro-max` |
| MCP specs | `.agent-toolkit/mcp/<server>.json` | `mcp-playwright`, `mcp-context7`, `mcp-github`, `mcp-figma`, `mcp-claude-design` |
| hooks | `.agent-toolkit/hooks/` | `session-reminder` |
| scripts and templates | `.agent-toolkit/deploy/`, `docker/` | `deploy-ubuntu`, `docker-local` |

A minimal install has none of the last four directories. They appear only
when a pack that ships them is selected.

## The pack format

Two shapes, and a pack can use both.

### A pointer into vendored content

The common case. The pack holds **no content** — it says which vendored file
to install and what to call it:

```jsonc
// catalog/packs/go/pack.json
{
  "id": "go",
  "title": "Go",
  "tier": "optional",
  "tags": ["backend"],
  "detect": ["go"],
  "summary": "Idiomatic Go: errors, concurrency, interfaces, project layout.",
  "vendor_maps": [
    { "vendor": "awesome-copilot",
      "files": [{ "from": "instructions/go.instructions.md", "to": "rules/GO.md" }] }
  ]
}
```

Content lives exactly once, under `vendor/`. Adding a pack costs ~400 bytes,
not a copy:

```
vendor/          9.4 MB   the actual content, fetched from pinned commits
catalog/packs/    328 KB   61 packs - mostly small JSON pointers
```

### Our own files

A `files/` directory next to `pack.json` is copied into `.agent-toolkit/`,
preserving structure:

```
catalog/packs/deploy-ubuntu/files/deploy/deploy.sh
  ->  .agent-toolkit/deploy/deploy.sh

catalog/packs/mcp-playwright/files/mcp/playwright.json
  ->  .agent-toolkit/mcp/playwright.json
```

This is where our own policy goes when an upstream is wrong or missing.
**Never** by editing the snapshot under `vendor/` — that fails
`uat vendor verify`, which is the point.

### Fields

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | must match the directory name |
| `title` | yes | shown in `uat catalog` and the interactive list |
| `tier` | yes | `core` / `recommended` / `optional` |
| `summary` | yes | one line: what it is and why you would want it |
| `tags` | no | free-form grouping, e.g. `backend`, `mcp`, `frontend` |
| `detect` | no | stack tokens that pre-select this pack |
| `requires` | no | pack ids pulled in automatically |
| `vendor_maps` | no | `{vendor, files:[{from, to}]}` — what to install from where |

## Writing a pack

```bash
mkdir -p catalog/packs/my-pack
$EDITOR catalog/packs/my-pack/pack.json
```

Then, before claiming it works:

```bash
./bin/uat doctor        # every vendor_map target must exist
./bin/uat catalog       # it appears, in the right tier
./bin/uat install --project /tmp/probe --agent claude-code \
                  --packs my-pack --yes --dry-run
./bin/uat-test
```

`doctor` fails if a `vendor_maps` entry points at a file that is not in the
snapshot — a typo in a `from` path is caught immediately, not at install
time in someone else's project.

## MCP specs and scope

An MCP pack ships a neutral spec at `files/mcp/<server>.json`. Each agent's
own config shape is derived from it, so one spec serves every tool.

```jsonc
{ "name": "playwright", "command": "npx", "args": ["-y", "@playwright/mcp@0.0.80"] }
{ "name": "figma", "url": "http://127.0.0.1:3845/mcp", "transport": "http" }
```

A spec needs either `command` (stdio) or `url` (http/sse).

### `scope`

| Value | Meaning |
|---|---|
| `project` *(default)* | written into the agent's project config, e.g. `.mcp.json` |
| `user` | **documented only** — never written into the project |

`scope: "user"` is for servers that belong to an individual account rather
than to the repository. `mcp-claude-design` is the case: it authenticates
against your own Anthropic plan, so an entry in a committed `.mcp.json` would
give every teammate a server that fails until they personally sign in — and
some of them may not be entitled to it at all.

The toolkit never writes outside the project, so it cannot add a user-scoped
server for you. It writes the spec, and `.agent-toolkit/mcp/README.md` carries
the exact command to run once per machine.

## The long tail

The two vendored rule libraries hold about 450 documents. Roughly 40 have
curated packs — the common stacks, with detection tokens and a reviewed
summary. The rest are niche clouds, single-vendor SDKs and stack-combination
files of varying quality.

Writing 450 packs would make `uat catalog` unusable, so the tail is reached
directly instead:

```bash
uat catalog --search wordpress
uat add-rule awesome-copilot:wordpress --project .
uat add-rule awesome-cursorrules:solidity --project . --as SOLIDITY.md
```

`add-rule` installs the document into `.agent-toolkit/rules/` and refreshes
`CORE.md` so the agent sees it.

`uat doctor` treats an unmapped **rule** document as normal, because
`add-rule` reaches it — but **fails** on an unmapped **skill**, which would
be dead weight nothing can install.

## Not vendored

Figma's skills are governed by the Figma Developer Terms rather than an
open-source licence, so they are not redistributed here. The `mcp-figma`
pack ships our own integration guide and tells you how to install Figma's
official skills from source yourself.

## Related

- [Vendoring & provenance](VENDORING.md) — where the content comes from
- [CLI reference](CLI.md#uat-catalog)
- [Architecture](ARCHITECTURE.md#one-store-many-pointers)
