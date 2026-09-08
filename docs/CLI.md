# CLI reference

```
uat [--verbose] <command> [options]
```

`uat` is `./bin/uat` from a toolkit checkout, or `.agent-toolkit/toolkit/uat`
inside an embedded project. `--verbose` is global and makes the change report
list unchanged files too, not only additions and conflicts.

Every command that touches a project takes `--project PATH` (default: the
current directory).

| Command | What it does |
|---|---|
| [`agents`](#uat-agents) | list supported coding agents |
| [`catalog`](#uat-catalog) | list packs and profiles; search vendored rules |
| [`detect`](#uat-detect) | show the detected stack and the evidence |
| [`install`](#uat-install) | install or extend the toolkit in a project |
| [`add-rule`](#uat-add-rule) | install one vendored rule document with no pack |
| [`workflow`](#uat-workflow) | planning progress and the next phase |
| [`status`](#uat-status) | what is installed, and local drift |
| [`uninstall`](#uat-uninstall) | remove only what the toolkit created |
| [`vendor`](#uat-vendor) | manage pinned upstream snapshots |
| [`embed`](#uat-embed) | copy the toolkit into a configured project |
| [`doctor`](#uat-doctor) | self-check this toolkit repository |

---

## `uat agents`

```
uat agents [--show ID]
```

Lists all 14 supported agents with their instruction file, whether they get a
skills mount, and how MCP is configured. `--show ID` prints one agent's
surfaces in full — every path and config key the installer will write.

```bash
uat agents
uat agents --show cursor
```

Each agent carries a `confidence` rating (green / yellow / red) for how well
its format has been verified against the vendor's own documentation. Formats
live in [`catalog/agents.json`](../catalog/agents.json), never in code — see
[Agent support](AGENT-SUPPORT.md).

---

## `uat catalog`

```
uat catalog [--unmapped] [--search TERM]
```

With no flags: every pack grouped by tier (`CORE`, `RECOMMENDED`,
`OPTIONAL`), then every profile with its pack count.

| Flag | What it does |
|---|---|
| `--search TERM` | search all ~450 vendored rule documents by name, including the ones with no pack |
| `--unmapped` | list vendored content that no pack exposes |

```bash
uat catalog
uat catalog --search wordpress
uat catalog --unmapped
```

The long tail is reachable with [`add-rule`](#uat-add-rule). See
[Packs & profiles](PACKS.md#the-long-tail).

---

## `uat detect`

```
uat detect [--project PATH]
```

Prints every detected token and the file that proves it — `react` because
`package.json requires react`, `pnpm` because `pnpm-lock.yaml` exists. It
reads manifests and lockfiles only; it never executes project code.

```bash
uat detect --project ~/app
```

```
Stack detection: /home/me/app
  node                         package.json
  react                        package.json requires react
  nextjs                       package.json requires next
  typescript                   tsconfig.json
  pnpm                         pnpm-lock.yaml
```

These tokens drive pack recommendation. A pack declares `"detect": ["go"]`
and is pre-selected when that token is present.

---

## `uat install`

```
uat install [--project PATH] [--agent ID]... [--mode MODE]
            [--profile NAME] [--packs ID...] [--add ID...] [--all]
            [--yes] [--force] [--dry-run] [--copy] [--replace]
            [--embed] [--with-vendor]
```

The main command. Installs `.agent-toolkit/` plus only the files your chosen
agents read.

### Choosing agents

| Flag | Effect |
|---|---|
| `--agent ID` | repeatable; `--agent claude-code --agent cursor` configures both |
| `--agent all` | configure every supported agent |

Aliases work: `--agent claude` resolves to `claude-code`.

### Choosing packs

Four ways. When more than one is given, the first matching row wins:

| Flag | Effect |
|---|---|
| `--all` | install every pack |
| `--packs ID...` | install exactly these; no detection, no recommendation |
| `--profile NAME` | install a named bundle (`core`, `frontend`, `nextjs`, `laravel-react`, `python-api`, `design`) |
| *(none of the above)* | detect the stack and recommend; interactive list unless `--yes` |

Any of the first three also suppresses the interactive pack list — you have
already said what you want.

`--add ID...` is additive on top of whichever of those you used, and is the
normal way to grow an install:

```bash
uat install --project . --agent claude-code --add go postgresql
```

Dependencies are expanded automatically, so selecting a pack pulls in what it
requires.

### Interaction mode

`--mode {thorough,focused,autonomous}` sets how many questions the agent
asks. Omitted on a fresh interactive install, you are prompted; omitted on a
re-install, the recorded mode is kept; omitted with `--yes`, it defaults to
`focused`. Recorded in `.agent-toolkit/project.json`. See
[Core policy](CORE-POLICY.md#interaction-modes).

### Extend vs replace

An install into a configured project **extends** it: previously installed
packs, configured agents and the recorded mode are all kept. So
`--add go` mid-project does not silently drop your Cursor config.

`--replace` drops packs and agents not named in this command, and starts the
recorded configuration over.

### Safety and output flags

| Flag | Effect |
|---|---|
| `--dry-run` | print every change, write nothing; also skips all prompts |
| `--yes`, `-y` | no prompts; use the recommendation |
| `--force` | overwrite conflicting files that the toolkit does not own |
| `--copy` | copy skills instead of symlinking (filesystems without symlink support) |

Without `--force`, an existing file the toolkit did not write is **kept and
reported**, never overwritten.

### Embedding

| Flag | Effect |
|---|---|
| `--embed` | also copy the toolkit into `.agent-toolkit/toolkit/` (~900 KB) |
| `--with-vendor` | with `--embed`, include every vendored upstream (~10 MB, fully offline) |

### Examples

```bash
# see everything first
uat install --project ~/app --agent claude-code --dry-run

# a Next.js project, two agents
uat install --project ~/app --agent claude-code --agent cursor --profile nextjs

# grow an existing install
uat install --project ~/app --agent claude-code --add go

# exact set, no detection, scriptable
uat install --project ~/app --agent codex --packs superpowers security docker --yes

# self-contained and offline-capable
uat install --project ~/app --agent claude-code --embed --with-vendor --yes

# start over
uat install --project ~/app --agent cursor --profile core --replace
```

---

## `uat add-rule`

```
uat add-rule VENDOR:NAME [--project PATH] [--as NAME.md] [--force] [--dry-run]
```

Installs any single vendored rule document into `.agent-toolkit/rules/` and
refreshes `CORE.md` so the agent sees it — without writing a pack for it.
This is how the ~410 uncurated rule documents stay reachable.

```bash
uat catalog --search wordpress
uat add-rule awesome-copilot:wordpress --project .
uat add-rule awesome-cursorrules:solidity --project . --as SOLIDITY.md
```

---

## `uat workflow`

```
uat workflow [--project PATH]
```

Shows the 14 planning phases, which have reports, which is next, and the
prompt to hand your agent to continue. Reads
`.agent-toolkit/reports/`, so progress survives across sessions, agents and
machines.

```
  done  01  discovery              reports/01-discovery.md
  done  02  business logic         docs/business-logic.md
  next  03  screens & flows        docs/screens.md
    -   04  stack                  docs/stack.md
```

See [Planning workflow](WORKFLOW.md).

---

## `uat status`

```
uat status [--project PATH]
```

Install timestamp, toolkit version, configured agents, pack count, skills
mode — and **drift**: files recorded in `installed.json` whose content hash
no longer matches, or that have gone missing.

```
Toolkit status: /home/me/app
  installed   2026-09-08T14:09:18+00:00
  version     0.1.0
  agents      claude-code
  packs       3
  skills      link

  no drift - installed files match the recorded install
```

Drift is information, not an error. An edited rule file is a legitimate local
override; `status` just makes sure you know it is there before a re-install
reports a conflict.

---

## `uat uninstall`

```
uat uninstall [--project PATH] [--keep-toolkit] [--dry-run]
```

Removes what the toolkit created, and only that. Ownership comes from
`installed.json`, so files you added or edited are reported and left alone.

| Flag | Effect |
|---|---|
| `--keep-toolkit` | leave `.agent-toolkit/` in place, remove the generated tool files |
| `--dry-run` | show what would go |

Always dry-run first.

---

## `uat vendor`

```
uat vendor list
uat vendor verify
uat vendor sync [--only ID...] [--force]
uat vendor add-local PATH --id ID --license LICENSE [--notes TEXT] [--force]
```

| Subcommand | What it does |
|---|---|
| `list` | pins, licences and verification state for every upstream |
| `verify` | re-hash every snapshot; a hand-edited file fails loudly |
| `sync` | fetch upstreams at their pinned commits |
| `add-local` | snapshot a local directory as a first-class vendor |

```bash
uat vendor list
uat vendor verify
uat vendor sync --only superpowers
uat vendor add-local ~/work/acme-rules --id acme --license "Proprietary - ACME"
```

Full detail, including why copying a directory into `vendor/` by hand does
not work, in [Vendoring & provenance](VENDORING.md).

---

## `uat embed`

```
uat embed [--project PATH] [--with-vendor] [--force]
```

Copies the toolkit into an already-configured project's
`.agent-toolkit/toolkit/`, so it can manage itself with no external checkout.
Same effect as `install --embed`, applied after the fact.

```bash
uat embed --project ~/app --with-vendor
```

---

## `uat doctor`

```
uat doctor
```

Self-checks **this repository**, not a project: registry loads, catalog
loads, every pack's vendor map points at a file that exists, every vendored
snapshot hashes to its pin, every vendored skill is reachable by some pack,
and no undeclared directory is sitting in `vendor/`.

```
Toolkit self-check
  ok  registry: 14 agents
  ok  catalog:  61 packs, 6 profiles
  ok  vendor superpowers: b36e082 verified
  ...
  ok  every vendored skill is reachable by a pack
  --  awesome-copilot: 157 rule file(s) with no pack - reachable via `uat add-rule`
healthy
```

Unmapped **rule** documents are reported as information (`--`), not failure —
`add-rule` reaches them. An unmapped **skill** is a failure: it is dead
weight nothing can install.

Run it before and after any change to this repository, alongside
`./bin/uat-test`.
