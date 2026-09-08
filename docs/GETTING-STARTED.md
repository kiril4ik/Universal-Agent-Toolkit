# Getting started

Fifteen minutes, one project, no global state.

## 1. Requirements

Python 3.9+ and git. Nothing else — no dependencies, no install step, no
build. `bin/uat` is a bash launcher that execs `python3`.

```bash
python3 --version
git --version
```

## 2. Clone the toolkit once

**Not into your project.** This repository is the factory. Keep one copy
anywhere and use it to configure as many projects as you like.

```bash
git clone <this repo> ~/tools/universal-agent-toolkit
cd ~/tools/universal-agent-toolkit
./bin/uat doctor     # catalog, registry and vendor snapshots all verify
```

`doctor` should end with `healthy`. If a vendor line says anything other than
`verified`, run `./bin/uat vendor sync` — see
[Vendoring & provenance](VENDORING.md).

## 2a. Optional: put `uat` on your PATH

Every example below writes `./bin/uat`, which always works from the checkout.
If you would rather type `uat` from anywhere, symlink the launcher into a
directory already on your PATH:

```bash
ln -s ~/tools/universal-agent-toolkit/bin/uat      ~/.local/bin/uat
ln -s ~/tools/universal-agent-toolkit/bin/uat-test ~/.local/bin/uat-test
uat doctor
```

The launcher resolves the symlink chain, so it finds its own `src/` and
`catalog/` no matter where the link lives. Adding the `bin/` directory to
PATH works too:

```bash
echo 'export PATH="$PATH:$HOME/tools/universal-agent-toolkit/bin"' >> ~/.zshrc
```

Nothing else is needed — there is no install step, and the toolkit never
writes to your shell configuration itself.

If you skip this, `uat install` will notice: a non-embedded install writes
bare `uat` into the project's `CORE.md`, and workflow phase 05 runs it to
install the stack's rule packs. The installer reports that under **Manual
steps required**, and on a terminal offers to create the symlink.

> The rest of these pages write `uat` for brevity. Read it as `./bin/uat`
> from a checkout, or `.agent-toolkit/toolkit/uat` in an embedded project.

## 3. Look before you install

```bash
./bin/uat agents                    # which coding agents are supported
./bin/uat catalog                   # every pack and profile
./bin/uat detect  --project ~/app   # what stack is in there, and the evidence
```

`detect` reads manifests (`package.json`, `composer.json`, `pyproject.toml`,
`go.mod`, …) and lockfiles, and prints the evidence for every token it found.
Those tokens are what pack recommendation runs on.

## 4. Dry run

Never necessary, always cheap:

```bash
./bin/uat install --project ~/app --agent claude-code --dry-run
```

It prints the plan, then every file it would create, change or skip. Nothing
is written. `--dry-run` also suppresses the interactive prompts, so it is
safe in scripts and CI.

## 5. Install

```bash
./bin/uat install --project ~/app --agent claude-code
```

Without `--yes`, and on a terminal, this is interactive. Two prompts:

**Interaction mode** — how many questions the agent should ask you:

```
How autonomous should the agent be?
  1  thorough    ask every question that materially affects the result
  2  focused     ask only blocking questions, use sensible defaults  (default)
  3  autonomous  decide independently; interrupt only for risky or ambiguous calls
```

**Pack selection** — a toggle list grouped by tier, with detected packs
pre-checked and the evidence shown:

```
Select packs to install
  toggle: numbers/ranges (1 3 5-8)   a=all  n=none  r=reset  Enter=accept

  CORE
     1 [x] Karpathy guidelines                 always
     2 [x] Security & OWASP                    always
     3 [x] Superpowers engineering skills      always
  RECOMMENDED
     4 [x] Accessibility (a11y)
     5 [ ] Ubuntu deployment
     6 [x] Docker & containers                 detected: docker
  ...
```

Then a plan, then `Proceed? [Y/n]`.

`--yes` skips both prompts and installs the recommendation. See
[Packs & profiles](PACKS.md) for what gets recommended and why.

> A bare `uat install --agent <id> --yes` with no `--profile`, `--packs` or
> detected stack installs the **core tier only** — three packs. That is a
> deliberate floor, not a full setup. For a real project, pick a profile or
> use the interactive list.

## 6. What landed

```
~/app/
├── .agent-toolkit/          <- everything the toolkit owns
│   ├── CORE.md              router: what exists, when to read it
│   ├── START-HERE.md        the workflow prompt, for agents without slash commands
│   ├── core/                safety, git, verification, interaction modes
│   ├── workflow/            the 14-phase planning workflow
│   ├── rules/               only the stack rules this project uses
│   ├── skills/              vendored skills, stored once
│   ├── reports/             one report per completed phase
│   ├── project.json         mode, agents, detected stack
│   └── installed.json       lockfile with content hashes
├── CLAUDE.md                <- a pointer, ~600 bytes
└── .claude/
    ├── skills -> ../.agent-toolkit/skills
    └── commands/            /plan, /plan-status, /plan-resume
```

Packs add their own directories when selected: `mcp/` (server specs),
`docker/`, `deploy/`, `hooks/`. A minimal install has none of them.

Verify:

```bash
./bin/uat status --project ~/app
```

## 7. Use it

```bash
cd ~/app
```

In Claude Code:

```
/plan build a client portal with invoicing
```

In any other agent, paste the prompt from `.agent-toolkit/START-HERE.md`.

The agent classifies the work, runs discovery, asks its questions, and stops
at the approval gate before writing code. Full sequence in
[Planning workflow](WORKFLOW.md).

Check progress from the shell at any time:

```bash
./bin/uat workflow --project ~/app
```

## Making the project self-contained

By default the project depends on your toolkit checkout for later changes
(adding a pack, uninstalling). `--embed` removes that dependency by copying
the toolkit into the folder it already owns:

```bash
./bin/uat install --project ~/app --agent claude-code --embed
```

```bash
cd ~/app
.agent-toolkit/toolkit/uat status  --project .
.agent-toolkit/toolkit/uat install --project . --agent claude-code --add go
```

| Mode | Adds to the project | Adding a pack later |
|---|---|---|
| default (external) | 0 | needs the toolkit checkout |
| `--embed` | ~900 KB | needs network (`uat vendor sync`) |
| `--embed --with-vendor` | ~10 MB | works fully offline, forever |

Embedding never creates a top-level folder — it goes inside
`.agent-toolkit/toolkit/`. You can also embed later, into an
already-configured project:

```bash
./bin/uat embed --project ~/app --with-vendor
```

## Changing your mind

Installing again **extends** what is there. Previous packs, agents and the
interaction mode are kept:

```bash
./bin/uat install --project ~/app --agent claude-code --add go postgresql
```

To start over deliberately:

```bash
./bin/uat install --project ~/app --agent cursor --profile core --replace
```

To remove everything the toolkit created — and only that:

```bash
./bin/uat uninstall --project ~/app --dry-run   # see it first
./bin/uat uninstall --project ~/app
```

Uninstall reads `installed.json` and removes files it recorded and still
owns. A file you edited is reported, not deleted.

## Next

- [CLI reference](CLI.md) — every command and flag
- [Packs & profiles](PACKS.md) — what is available and how selection works
- [Agent support](AGENT-SUPPORT.md) — what your specific tool receives
- [Troubleshooting](TROUBLESHOOTING.md) — when the agent ignores it anyway
