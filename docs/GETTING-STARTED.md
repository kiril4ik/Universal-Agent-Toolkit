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

## 2. Clone the toolkit and install

Keep the checkout outside your application. One checkout can configure many
projects.

### macOS / Linux

```bash
git clone https://github.com/kiril4ik/Universal-Agent-Toolkit.git ~/tools/universal-agent-toolkit
cd ~/tools/universal-agent-toolkit
./bin/uat doctor
./bin/uat install --project ~/code/my-app --agent claude-code
```

### Windows PowerShell

```powershell
git clone https://github.com/kiril4ik/Universal-Agent-Toolkit.git "$HOME/tools/universal-agent-toolkit"
cd "$HOME/tools/universal-agent-toolkit"
.\bin\uat.cmd doctor
.\bin\uat.cmd install --project "$HOME/code/my-app" --agent claude-code
```

`doctor` should end with `healthy`. See [Vendoring & provenance](VENDORING.md)
if snapshot verification fails. Add `--dry-run` to preview installation or
`--yes` to accept the recommended selection without prompts.

## 2a. PATH setup

### Windows: automatic on first installation

A successful non-embedded `install` adds the checkout's `bin` directory to
**your user PATH** if `uat` is not already available. This also happens with
`--yes`; no administrator access is needed. Existing PATH entries are
preserved, and repeat installs do not add duplicates. `--no-path` skips this
setup; `--dry-run`, failed installs, and `--embed` do not change PATH.

Restart your terminal application (and IDE if its terminal is embedded), or
refresh the current PowerShell session:

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
uat doctor
```

An already-running shell retains its inherited environment; see Microsoft's
[environment documentation](https://learn.microsoft.com/en-us/windows/win32/procthread/environment-variables).

For manual setup, open **Edit environment variables for your account**, edit
**Path**, and add the full checkout `bin` path, for example
`C:\Users\you\tools\universal-agent-toolkit\bin`. Restart your terminal.
Remove that entry to undo setup, or update it if you move the checkout.
Project uninstall leaves this shared CLI entry available for other projects.

### macOS / Linux

The first interactive install offers to symlink `uat` into a writable
user-owned directory already on PATH. `--yes` and `--no-path` skip that prompt.
For manual setup:

```bash
mkdir -p ~/.local/bin
ln -s ~/tools/universal-agent-toolkit/bin/uat ~/.local/bin/uat
ln -s ~/tools/universal-agent-toolkit/bin/uat-test ~/.local/bin/uat-test
export PATH="$HOME/.local/bin:$PATH"
uat doctor
```

To persist the `export`, add it once to `~/.zshrc` (zsh) or `~/.bashrc` (Bash),
then open a new terminal. The launcher resolves symlinks to find its catalog.

The examples below use `./bin/uat` from the checkout. In Windows PowerShell,
substitute `.\bin\uat.cmd` and use paths such as `"$HOME/code/my-app"`.
After PATH setup, use `uat` from anywhere. For embedded projects, use
`.agent-toolkit/toolkit/uat` on Unix or
`.\.agent-toolkit\toolkit\uat.cmd` in Windows PowerShell.

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

**Pack selection** — a keyboard checklist ordered by tier, with detected packs
pre-checked and the evidence shown:

```
Select skills and packs to install
Up/Down: move  Space: toggle  Enter: accept
Esc: cancel  a: all  n: none  r: reset

> [x] Karpathy guidelines (core)
  [x] Security & OWASP (core)
  [x] Superpowers engineering skills (core)
  [x] Accessibility (a11y) (recommended)
  [ ] Ubuntu deployment (recommended)
  [x] Docker & containers (recommended) detected: docker
  ...
```

Use **Up/Down** to move, **Space** to select or deselect, and **Enter** to
confirm. **Esc** or **Ctrl+C** cancels installation. The list scrolls with the
cursor, so no item numbers are needed. **A** selects all, **N** clears the
selection, and **R** restores recommendations. Dependencies are added when
you confirm. Skills are selected through their installable packs.

The same controls work in Windows PowerShell/Command Prompt and macOS/Linux
terminals. For automation or redirected input/output, use `--yes`,
`--packs ID ...`, or `--profile NAME`.

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
