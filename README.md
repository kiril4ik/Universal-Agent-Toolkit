# Universal Agent Toolkit

Install AI coding rules, skills, MCP servers and a project planning workflow
into any project — **for the coding agent you actually use, and nothing else.**

```bash
./bin/uat install --project ~/code/my-app --agent claude-code
```

That creates exactly one folder, `.agent-toolkit/`, plus the two or three
files Claude Code itself needs. It does not create `.cursor/`, `.windsurf/`,
`.clinerules`, `GEMINI.md` or anything else you did not ask for.

## Why

Every coding agent has its own instruction file, rules directory and MCP
configuration. Every project needs different rules. The usual result is a
project root littered with config for eight tools, none of which is current.

This repository separates two jobs:

1. **A broad library, maintained once** — pinned upstream rules, skills and
   MCP definitions, verified against their source commits.
2. **A narrow install, per project** — detect the stack, copy only what that
   project needs, generate only the surfaces that one agent reads.

## Where does this repository live?

**Not inside your project.** This repo is the *factory* — `bin/ src/ catalog/
vendor/` are build material, not something you copy into an app. Keep it once,
anywhere:

```bash
git clone <this repo> ~/tools/universal-agent-toolkit
~/tools/universal-agent-toolkit/bin/uat install --project ~/code/my-app --agent claude-code
```

Your project receives one folder and its agent files. Nothing else.

### If you want the project to be fully self-contained

Add `--embed`. The toolkit copies *itself* inside the folder it already owns,
so the project can manage its own configuration with no external checkout:

```bash
uat install --project ~/code/my-app --agent claude-code --embed
```

```
my-app/.agent-toolkit/toolkit/     <- the CLI + catalog, ~380 KB
my-app/.agent-toolkit/toolkit/uat  <- run it from the project
```

```bash
cd ~/code/my-app
.agent-toolkit/toolkit/uat status  --project .
.agent-toolkit/toolkit/uat install --project . --agent claude-code --add go
```

| Mode | Adds | Adding a new pack later |
|---|---|---|
| default (external) | 0 | needs the toolkit checkout |
| `--embed` | ~380 KB | needs network (`uat vendor sync`) |
| `--embed --with-vendor` | ~8.2 MB | works fully offline, forever |

Either way the project root only ever gains `.agent-toolkit/` plus the files
your chosen agent reads. Embedding never adds a top-level folder.

You can also embed later, into an already-configured project:

```bash
uat embed --project ~/code/my-app --with-vendor
```

## Quick start

```bash
./bin/uat agents                    # 14 supported agents and what each one gets
./bin/uat catalog                   # 45 packs and 6 profiles
./bin/uat detect  --project ~/app   # what stack is in there, and the evidence
./bin/uat install --project ~/app --agent claude-code
```

Add `--dry-run` to see every file that would change before anything does.

```bash
./bin/uat install --project ~/app --agent cursor --profile nextjs
./bin/uat install --project ~/app --agent claude-code --agent cursor
./bin/uat install --project ~/app --agent claude-code --add go   # extends; keeps the rest
./bin/uat install --project ~/app --agent cursor --profile core --replace   # starts over
./bin/uat workflow  --project ~/app     # planning progress and next step
./bin/uat status    --project ~/app     # what is installed, and local drift
./bin/uat uninstall --project ~/app     # removes only what it created
```

Interactive by default: it asks for an interaction mode, then shows a
checklist of packs with the detected stack marked. `--yes` skips both.

## What a project gets

```
my-app/
├── .agent-toolkit/          <- everything lives here
│   ├── CORE.md              routing file: what exists, when to read it
│   ├── core/                safety, git, verification, interaction modes
│   ├── workflow/            the 12-phase planning workflow
│   ├── rules/               only the stack rules this project uses
│   ├── skills/              vendored skills, stored once
│   ├── mcp/                 neutral server specs + setup status
│   ├── deploy/  docker/     provisioning and local-dev templates
│   ├── reports/             one report per completed phase
│   ├── project.json         mode, agents, detected stack
│   ├── installed.json       lockfile with content hashes
│   └── toolkit/             the toolkit itself (only with --embed)
├── CLAUDE.md                <- a pointer, ~600 bytes
├── .claude/skills -> ../.agent-toolkit/skills
└── .mcp.json
```

Skills are **symlinked**, not copied, so nothing is duplicated on disk.
Use `--copy` on filesystems without symlink support.

## Using it after installing

Four layers, weakest to strongest. Installing gives you all four.

**1. Passive — the agent reads it on its own.** `CLAUDE.md` (or `AGENTS.md`,
`.cursor/rules/`) is auto-loaded and points at `.agent-toolkit/CORE.md`, which
routes to the workflow, the safety rules and the stack rules. This works, but
relies on the agent choosing to follow a pointer.

**2. Active — you trigger it.** With Claude Code:

```
/plan add multi-tenant billing      start the workflow at triage
/plan-status                        progress, without advancing
/plan-resume                        continue where it stopped
```

With any other agent, paste the prompt from `.agent-toolkit/START-HERE.md`:

> Read `.agent-toolkit/workflow/README.md` and run the planning workflow.
> Start with triage, tell me the classification and which phases apply, then
> work through them in order. Stop at the gate for my approval.

**3. Enforced — the `session-reminder` hook.** Installed by every profile. It
registers a `SessionStart` hook that injects the non-negotiables into context
at the start of *every* session: run triage first, no implementation before the
gate, read `SAFETY.md` before touching data, verify before claiming done. It
also reports how many phases are complete and which is next.

This is the layer that makes the difference between rules being *available* and
rules being *used* — it is the same mechanism Superpowers itself uses. Your
tool will ask you to approve the hook the first time; that prompt is expected.

```bash
uat install --project . --agent claude-code --add session-reminder
```

**4. Verifiable — you can check.** `uat workflow --project .` shows which
phases have reports and what comes next. Progress lives in
`.agent-toolkit/reports/`, so it survives across sessions, agents and machines.

### A normal session

```bash
uat install --project ~/code/my-app --agent claude-code --embed   # once
cd ~/code/my-app
```

Then, in the agent: `/plan build a client portal with invoicing`

It classifies the work, runs discovery, and asks its questions. Somewhere
around phase 04 it decides the stack; at phase 05 it runs
`uat install --add <pack>` so the rules for that stack land in the project.
At phase 10 it hands to `writing-plans`. At phase 11 it stops and waits for
you. Only after you approve does phase 12 start writing code.

Between sessions, `/plan-resume` picks up from the reports.

### If the agent ignores it anyway

Check, in order:

1. `uat status --project .` — is it actually installed?
2. Is `session-reminder` in the pack list? Add it if not.
3. Did you approve the hook when your tool prompted?
4. For non-Claude tools, is the instruction file the one your tool actually
   reads? `uat agents --show <id>` lists the paths it uses.

## Supported agents

Claude Code, Cursor, Codex, GitHub Copilot / VS Code, Gemini CLI, Windsurf,
Cline, Roo Code, JetBrains Junie, OpenCode, Aider, Amp, Zed, Kilo Code.

Every tool-specific path and config key lives in
[`catalog/agents.json`](catalog/agents.json). A format change is a one-line
edit there, never a code change. Each agent carries a `confidence` rating for
how well its format is verified — check it with `uat agents --show cursor`.

Claude Code (`.claude/skills/`) and Codex (`.agents/skills/`) have native skill
discovery, so both get a skills mount. Every other agent gets the same content
as plain Markdown it can read.

An install into a configured project **extends** it: previous packs, agents and
interaction mode are kept, so `--add go` mid-project does not quietly discard
your Cursor config. Use `--replace` to start over deliberately.

## The planning workflow

`.agent-toolkit/workflow/` holds a twelve-phase sequence any agent can follow:

| # | Phase | Skill it delegates to |
|---|---|---|
| 00–01 | triage, discovery | — |
| 02 | business logic | `brainstorming` |
| 03 | screens & flows | — |
| 04–05 | stack, rules | — |
| 06 | architecture | `brainstorming` |
| 07–08 | content, design | `ui-ux-pro-max`, Figma MCP |
| 09 | environments | — |
| 10 | plan | **`writing-plans`** |
| 11 | **gate** | — |
| 12 | execute | **`subagent-driven-development`** |

**Design runs after architecture, deliberately.** Screens & flows (03) give
architecture what it needs early; visual design (08) then works against a
chosen component library and a data model that can actually serve the screens,
instead of being redone when they arrive.

**The workflow sequences Superpowers rather than competing with it.** Phase 10
does not define a plan format — it hands over to `writing-plans`, so there is
one plan, in one place, that the execution skills can find. Phase 12 hands over
to `subagent-driven-development`.

Skills were written to run standalone, so four of their instructions are
superseded inside the workflow — classify once in triage, batch questions, one
approval gate, and their terminal-state rule does not apply. The complete list
is the "Precedence" section of `workflow/README.md`, and tests assert it covers
every known conflict. **No vendored file is edited to achieve this.**

Triage picks the depth: a one-line fix runs discovery and stops; a new product
runs everything. **Phase 11 is never skipped** — nothing is implemented until
the artifacts are checked against each other and a human approves.

### How you actually start it

Installing generates the trigger, not just the documentation.

**Claude Code** gets real slash commands:

```
/plan <what you want to build>    run the workflow from triage
/plan-status                      show progress without advancing
/plan-resume                      pick up where it stopped
```

**Every other agent** gets the same instruction as a prompt, in
`.agent-toolkit/START-HERE.md`:

> Read `.agent-toolkit/workflow/README.md` and run the planning workflow.
> Start with triage, tell me the classification and which phases apply, then
> work through them in order. Stop at the gate for my approval.

Check progress from the shell at any time:

```bash
uat workflow --project .
```

```
  done  01  discovery              reports/01-discovery.md
  done  02  business logic         docs/business-logic.md
  next  03  screens & flows        docs/screens.md
    -   04  content                docs/content/
```

Phases 06 and 07 close the loop: once the stack is decided, the workflow tells
the agent to run `uat detect` and `uat install --add <pack>` so the rules for
that stack land in the project. You start with core packs and grow into the
stack you actually chose — not the one you guessed at install time.

## Provenance is enforced, not claimed

Every vendored file is fetched from a pinned commit and hashed:

```bash
./bin/uat vendor list      # pins, licences and verification state
./bin/uat vendor verify    # re-hashes; a hand-edited snapshot fails loudly
./bin/uat vendor sync      # fetch at the pinned commits
```

| Upstream | Licence | What |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | MIT | 14 engineering-discipline skills |
| [github/awesome-copilot](https://github.com/github/awesome-copilot) | MIT | 193 technology instruction guides |
| [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) | CC0 | 257 community rules (gap filling) |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | MIT | React / Next.js best practices |
| [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) | MIT | Interface quality checklist |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | MIT | Design intelligence and palettes |
| [emavv/karpathy-guidelines](https://github.com/emavv/karpathy-guidelines) | MIT | Anti-overcomplication guardrails |

Vendored content is **never edited**. Our own policy lives in `catalog/core/`.

### How vendor/ and packs relate

They are not two copies of the same thing — it is one store and many pointers.

```
vendor/          9.4 MB   the actual content, fetched from pinned commits
catalog/packs/    328 KB   60 packs - each one a small JSON pointer into vendor/
```

A pack does not contain content. It says *which* vendored file to install,
what to call it, and when it applies:

```jsonc
{ "id": "go", "detect": ["go"],
  "vendor_maps": [{ "vendor": "awesome-copilot",
    "files": [{ "from": "instructions/go.instructions.md", "to": "rules/GO.md" }] }] }
```

So content lives exactly once. Adding a pack costs ~400 bytes, not a copy.

### Vendoring your own content

Not everything worth vendoring is a public git repo — house style guides,
a company's internal rules, a skill you wrote:

```bash
uat vendor add-local ~/work/acme-rules --id acme --license "Proprietary - ACME"
```

It snapshots the directory into `vendor/acme/`, content-hashes it, and
registers it in `catalog/vendor.json`. From then on it is treated exactly like
a git upstream: `vendor verify` catches edits to the snapshot, and
`vendor sync` re-copies from the original when that path still exists (a
teammate who cloned the repo keeps the snapshot without needing your folder).

Just copying a directory into `vendor/` by hand does **not** work — it would
be invisible to sync, verify and every pack. `uat doctor` fails if it finds
one, and tells you to register or delete it.

### Packs are curated; nothing vendored is unreachable

All 24 vendored *skills* have packs. The two rule libraries hold 450
documents, of which ~40 have curated packs — the common stacks, with stack
detection and a reviewed summary. The rest are the long tail: niche clouds,
single-vendor SDKs, and stack-combo files whose quality varies.

Writing 450 packs would make `uat catalog` unusable, so the long tail is
reachable directly instead:

```bash
uat catalog --search wordpress          # search all 450 by name
uat catalog --unmapped                  # everything with no pack
uat add-rule awesome-copilot:wordpress --project .
```

`add-rule` installs any vendored document into `.agent-toolkit/rules/` and
refreshes the router so the agent sees it. `uat doctor` **fails** if a
vendored *skill* has no pack — that is dead weight — but treats an unmapped
rule document as normal, because `add-rule` reaches it.

**Not vendored:** Figma's skills are governed by the Figma Developer Terms
rather than an open-source licence, so the `mcp-figma` pack ships our own
integration guide and tells you how to install theirs from source.

## Deployment

The `deploy-ubuntu` pack ships working, tested bash:

- `inspect-server.sh` — read-only audit; run it before touching any server
- `provision-clean.sh` — fresh Ubuntu to ready-to-host
- `provision-existing.sh` — adds an app to a server already running things:
  refuses a taken port, writes exactly one new nginx site, never modifies an
  existing config, validates before reloading, never touches a database
- `deploy.sh` — atomic symlink release with health check and auto-revert
- `rollback.sh` — return to a previous release

Verified by running them on Ubuntu 24.04, including `nginx -t` on the
generated config.

## Design rules

- **One folder.** Everything installed lives in `.agent-toolkit/`.
- **Only what is asked for.** Selecting one agent never creates another's files.
- **Pointers, not copies.** Tool files route to the canonical content.
- **No silent overwrite.** Existing files are kept and reported; `--force` is explicit.
- **Nothing global.** No global installs, ever.
- **Data is valuable.** Destructive operations are gated, including locally.
- **Evidence before claims.** See `catalog/core/VERIFICATION.md`.

## Requirements

Python 3.9+ and git. No dependencies, no install step, no build.

## Tests

```bash
./bin/uat-test     # 50 tests
./bin/uat doctor   # verify catalog, registry and vendored snapshots
```

## Adding things

- **A new agent** — add an entry to `catalog/agents.json`.
- **A new rule pack** — add `catalog/packs/<id>/pack.json`; map a vendored file
  or add your own under `files/`.
- **A new upstream** — add it to `catalog/vendor.json` and run `uat vendor sync`.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
