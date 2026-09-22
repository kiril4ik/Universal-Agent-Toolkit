# Toolkit Setup and Optional Ponytail Design

## Goal

Make Ponytail available without installing it by default, and add a
cross-platform `uat setup` command that installs a runnable per-user copy of
the toolkit before projects use the normal current-directory command:
`uat install --agent <id>`.

## Scope

This change has two related user-facing outcomes:

1. Ponytail remains a supported pack and vendored dependency, but is not part
   of the core recommendation or core profile. It is installed only when the
   user explicitly selects it, selects all packs, or selects a profile that
   names it.
2. A toolkit checkout can bootstrap itself into the platform's per-user
   application location and make `uat` available on PATH through `uat setup`.

The installer continues to write project configuration only inside the target
project. `uat setup` changes only the user's toolkit installation and PATH
configuration; it does not modify a project.

## Ponytail selection model

`catalog/packs/ponytail/pack.json` changes from `core` to `optional`.
`catalog/profiles/core.json` no longer names `ponytail`.

This makes all ordinary recommendation paths omit Ponytail:

- `catalog.recommend()` does not select it.
- Interactive install shows it unchecked.
- `--yes` uses a recommendation without it.
- `--profile core` does not include it.

Explicit selection remains supported through `--add ponytail`,
`--packs ponytail`, `--all`, and any named profile that explicitly includes
the pack. The pack's rule and all vendored skills remain unchanged.

## Setup command

### Command shape

```text
uat setup [--dry-run] [--force]
```

The command uses the current toolkit root resolved from the launcher. It
requires the source root to contain the runtime directories and launchers
needed by the standalone checkout layout. It is intentionally separate from
`install`: setup prepares the reusable CLI, while install configures a
project.

`--dry-run` reports planned file copies, launcher registration, and shell
profile changes without writing. Existing divergent destination files are
preserved unless `--force` is supplied. Re-running setup against identical
content is a no-op.

### Copied runtime

The per-user copy contains the runnable toolkit, not repository-only material:

- `src/`
- `catalog/`
- `vendor/`
- `VERSION` and `LICENSE` when present
- `bin/uat` and `bin/uat.cmd` when present

This keeps every catalog pack available offline after setup. The source
checkout's `.git/`, tests, and documentation are not copied into the runtime
installation.

### Platform destinations

The destination is derived from the host platform and user environment:

| Platform | Application copy | PATH entry |
|---|---|---|
| Windows | `%LOCALAPPDATA%\\Universal-Agent-Toolkit` | application `bin/` added to the user PATH through the registry |
| macOS | `~/Library/Application Support/Universal-Agent-Toolkit` | `~/.local/bin/uat` launcher and `~/.local/bin` in the user shell profile |
| Linux/other Unix | `~/.local/share/universal-agent-toolkit` | `~/.local/bin/uat` launcher and `~/.local/bin` in the user shell profile |

On Unix, the launcher in `~/.local/bin` points at the copied application's
`bin/uat`. The command updates one appropriate user startup file with a
stable, marked PATH export and never duplicates that block. The current shell
cannot be modified by a child process, so setup prints the command's
completion message and tells the user to open a new shell (or export the path
for the current one).

Windows reuses the existing user-scoped PATH registry helper and preserves
machine PATH entries and unrelated user entries. It also refreshes the current
process environment where possible, while explaining that already-running
terminal applications may need to be restarted.

### Safety and failure behavior

- Setup never moves or deletes the source checkout.
- Setup never edits project files.
- Existing non-toolkit launchers and unrelated PATH entries are preserved.
- A destination conflict is reported and leaves the existing file untouched
  unless `--force` is supplied.
- A failed copy or PATH update returns a user-facing error through the normal
  CLI error path.
- The default destination can be overridden internally in tests, but the user
  command intentionally keeps platform defaults simple.

## Documentation changes

The first setup method in `README.md` and `docs/GETTING-STARTED.md` becomes:

1. Clone the toolkit checkout.
2. Run the platform-specific `setup` command from that checkout.
3. Change directory into the application project.
4. Run `uat install --agent <id>` with no project flag.

The docs still show `--project PATH` for automation and explain that the
interactive pack picker supports all/none/reset shortcuts. Existing PATH
sections are consolidated so they describe `uat setup` rather than presenting
manual symlinking as the primary flow.

`docs/CLI.md` gains the setup command, flags, destination table, and examples.
`docs/PACKS.md` and the relevant README text describe Ponytail as optional.

## Testing strategy

Tests will prove behavior rather than implementation details:

- catalog recommendation and core profile omit Ponytail;
- explicit Ponytail installation still writes its rule and all expected skills;
- platform destination resolution returns the documented locations;
- setup copies the runnable runtime and does not copy repository-only paths;
- dry-run setup writes nothing;
- repeated Unix PATH setup is idempotent and preserves unrelated profile text;
- Windows setup calls the existing user PATH helper with the copied app's
  `bin` directory;
- the parser exposes `setup`, `--dry-run`, and `--force`.

The repository's full verification remains authoritative:

```bash
./bin/uat-test
./bin/uat doctor
./bin/uat install --project /tmp/probe --agent claude-code --yes --dry-run
```
