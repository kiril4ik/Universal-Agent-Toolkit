# Getting started

Fifteen minutes, one project. Windows setup also registers the CLI on your user PATH.

## 1. Requirements

Python 3.9+ and Git. No Python packages or build step. The command is **`uat`**;
install the toolkit by cloning this repository.

### macOS

With [Homebrew](https://brew.sh/) installed:

```bash
brew install python git
python3 --version
git --version
```

### Linux / WSL

Ubuntu and Debian:

```bash
sudo apt update
sudo apt install python3 git
```

Fedora:

```bash
sudo dnf install python3 git
```

Check `python3 --version` is at least 3.9. WSL uses these Linux instructions
and its own checkout and PATH.

### Windows (PowerShell or Command Prompt)

Install [Python for Windows](https://www.python.org/downloads/windows/) and
[Git for Windows](https://git-scm.com/install/windows). For Git, the WinGet
package is `Git.Git` (`winget install --id Git.Git -e`). Enable Python's PATH
option if offered by its installer. Open a new terminal and check:

```powershell
py -3 --version
git --version
```

The launcher tries `py -3`, then `python`, then `python3`, requiring Python
3.9+. It is a `.cmd` file usable from PowerShell and Command Prompt, without
a PowerShell execution-policy change. Bash-based packs, such as the session
reminder, still need Bash; use Git Bash or WSL for those scripts. Ubuntu
deployment scripts run on Ubuntu.

## 2. Set up the reusable CLI

Keep the git checkout outside your application. One checkout can configure
many projects. `uat setup` copies the runnable toolkit to a standard per-user
location and makes its launcher available on PATH.

### macOS / Linux

```bash
git clone https://github.com/kiril4ik/Universal-Agent-Toolkit.git ~/tools/universal-agent-toolkit
cd ~/tools/universal-agent-toolkit
./bin/uat setup
```

On macOS the application copy is placed in
`~/Library/Application Support/Universal-Agent-Toolkit`; on Linux it is
placed in `~/.local/share/universal-agent-toolkit`. Both platforms get a
launcher at `~/.local/bin/uat`, and setup adds that directory to your shell
profile. Open a new shell before using bare `uat`.

### Windows PowerShell

```powershell
git clone https://github.com/kiril4ik/Universal-Agent-Toolkit.git "$HOME/tools/universal-agent-toolkit"
cd "$HOME/tools/universal-agent-toolkit"
.\bin\uat.cmd setup
```

Windows copies the application to `%LOCALAPPDATA%\Universal-Agent-Toolkit` and
adds its `bin` directory to your user PATH without administrator access.
Restart PowerShell (or refresh its PATH) before using bare `uat`.

Use `--dry-run` to preview setup and `--force` to replace a conflicting file:

```bash
./bin/uat setup --dry-run
./bin/uat setup --force
```

`uat doctor` should end with `healthy`. See [Vendoring & provenance](VENDORING.md)
if snapshot verification fails. For manual setup, add the copied application's
launcher directory to PATH; do not move the git checkout.

The examples below use `uat` from PATH on every operating system. For embedded
projects, use `.agent-toolkit/toolkit/uat` on Unix or
`.\.agent-toolkit\toolkit\uat.cmd` in Windows PowerShell.

## 3. Look before you install

```bash
uat agents                    # which coding agents are supported
uat catalog                   # every pack and profile
uat detect  --project ~/app   # what stack is in there, and the evidence
```

`detect` reads manifests (`package.json`, `composer.json`, `pyproject.toml`,
`go.mod`, …) and lockfiles, and prints the evidence for every token it found.
Those tokens are what pack recommendation runs on.

## 4. Dry run

Never necessary, always cheap:

```bash
cd ~/app
uat install --agent claude-code --dry-run
```

It prints the plan, then every file it would create, change or skip. Nothing
is written. `--dry-run` also suppresses the interactive prompts, so it is
safe in scripts and CI.

## 5. Install

```bash
cd ~/app
uat install --agent claude-code
```

Without `--yes`, and on a terminal, setup is progressive. It asks about the
project kind, coding tools, interaction mode, planning, technology additions,
acceptance, visual validation, database backups, and image generation before
showing the capability checklist. Every prompt has a default and a matching
CLI flag for silent installs.

**Single-choice settings** — move with **Up/Down** and press **Enter**. The
cursor starts on the default or previously configured value:

```
How autonomous should the agent be?
  Up/Down=move  Enter=select  Esc=cancel

  thorough    ask every question that materially affects the result
> focused     ask only blocking questions; use sensible defaults  default
  autonomous  interrupt only for risky or ambiguous calls
```

**Coding tools and capabilities** — move with **Up/Down**, toggle any number
of choices with **Space**, then press **Enter**. Capabilities are grouped by
purpose, with detected packs pre-checked and the evidence shown:

```
Select packs to install
  Up/Down=move  Space=toggle  Enter=accept  Esc=cancel
  a=all  n=none  r=reset

  ENGINEERING
>  [x] Engineering principles (SOLID, DRY, KISS)  default
   [x] Karpathy guidelines                 default
   [ ] Ponytail minimal-change engineering (optional; select it explicitly)
  BROWSER QUALITY
   [x] Playwright MCP (browser)            detected: frontend
  ...
```

Use **Up/Down** to move, **Space** to select or deselect, and **Enter** to
confirm. **Esc** or **Ctrl+C** cancels installation. The list scrolls with the
cursor and keeps the category headings visible. **A** selects all, **N** clears
the selection, and **R** restores recommendations. Dependencies are added when
you confirm. Skills are selected through their installable packs.

The same controls work in Windows PowerShell/Command Prompt and macOS/Linux
terminals. For automation or redirected input/output, use `--yes`,
`--packs ID ...`, or `--profile NAME`.

Then a plan, then `Proceed? [Y/n]`.

`--yes` accepts the policy defaults and installs the recommendation. Use flags
such as `--planning off`, `--technology-additions auto`, `--acceptance full`,
`--db-backups finish`, and `--image-generation ask` to make silent setup exact. See
[Packs & profiles](PACKS.md) for what gets recommended and why.

> A bare `uat install --agent <id> --yes` with no `--profile`, `--packs` or
> detected stack installs the **core tier only** — four packs. That is a
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
uat status --project ~/app
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
uat workflow --project ~/app
```

## Making the project self-contained

By default the project depends on your toolkit checkout for later changes
(adding a pack, uninstalling). `--embed` removes that dependency by copying
the toolkit into the folder it already owns:

```bash
uat install --project ~/app --agent claude-code --embed
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
uat embed --project ~/app --with-vendor
```

## Changing your mind

Installing again **extends** what is there. Previous packs, agents and the
interaction mode are kept:

```bash
uat install --project ~/app --agent claude-code --add go postgresql
```

To start over deliberately:

```bash
uat install --project ~/app --agent cursor --profile core --replace
```

To remove everything the toolkit created — and only that:

```bash
uat uninstall --project ~/app --dry-run   # see it first
uat uninstall --project ~/app
```

Uninstall reads `installed.json` and removes files it recorded and still
owns. A file you edited is reported, not deleted.

## Next

- [CLI reference](CLI.md) — every command and flag
- [Packs & profiles](PACKS.md) — what is available and how selection works
- [Agent support](AGENT-SUPPORT.md) — what your specific tool receives
- [Troubleshooting](TROUBLESHOOTING.md) — when the agent ignores it anyway
