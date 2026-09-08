# Troubleshooting

## The agent ignores the rules

The most common report, and almost always one of four things. Check them in
order.

### 1. Is it actually installed?

```bash
uat status --project .
```

If this errors, nothing is installed in this directory. If it prints a pack
count of `3`, you have the core tier only — a bare
`install --yes` with no profile and no detectable stack installs the floor,
not a setup.

### 2. Is `session-reminder` in the pack list?

This is the layer that matters most, and it is easy to miss because it is not
in the core tier.

```bash
uat install --project . --agent claude-code --add session-reminder
```

Without it, the rules are *available* — the agent has to choose to follow a
pointer from `CLAUDE.md` to `CORE.md` to the rule that applies. With it, a
`SessionStart` hook injects the non-negotiables into context at the start of
every session: run triage first, no implementation before the gate, read
`SAFETY.md` before touching data, verify before claiming done. It also
reports how many phases are complete and which is next.

Every profile includes it. A hand-picked `--packs` list may not.

### 3. Did you approve the hook?

Claude Code asks for approval the first time a project registers a hook. That
prompt is expected — and if it was dismissed, the hook silently never runs.

Check `.claude/settings.json` contains a `SessionStart` entry pointing at
`.agent-toolkit/hooks/session-start.sh`, then start a fresh session and
approve when asked.

### 4. Is it the file your tool actually reads?

```bash
uat agents --show <id>
```

Tools disagree about this constantly, and a rules file in the wrong place is
invisible rather than broken. If the path shown is not what your tool's
documentation says, the entry in
[`catalog/agents.json`](../catalog/agents.json) is wrong — fix it there and
open an issue. Agents with `confidence: medium` are the likely candidates.

---

## Install problems

### "Existing file kept" in the report

Working as designed. The toolkit never overwrites a file it does not own.
Look at the file — if it is yours and you want to keep it, nothing to do. If
you want the toolkit's version:

```bash
uat install --project . --agent claude-code --force
```

`--force` is deliberately explicit and never implied.

### `--add` seems to have dropped my other packs

It should not. An install into a configured project **extends** it: previous
packs, agents and interaction mode are all kept.

```bash
uat status --project .     # what is actually recorded
```

If packs really are missing, check whether the command included `--replace`,
which drops anything not named in that command.

### Symlink creation failed

Skills are symlinked so nothing is duplicated on disk. On filesystems without
symlink support (some Windows setups, some network mounts):

```bash
uat install --project . --agent claude-code --copy
```

### The interactive picker never appeared

It appears only when **all** of these hold: stdin is a terminal, and you
passed none of `--yes`, `--dry-run`, `--packs`, `--profile` or `--all`. Any
of those means you already said what you wanted.

### `unknown profile 'x'`

```bash
uat catalog     # profiles are listed at the bottom
```

Six exist: `core`, `frontend`, `nextjs`, `laravel-react`, `python-api`,
`design`.

---

## Detection problems

### My stack was not detected

```bash
uat detect --project .
```

The output shows every token and the file that proves it. Detection reads
manifests and marker paths only — it never executes project code — so a
dependency installed but not declared, or a monorepo whose manifests are one
level down, will not be seen.

Just name the packs yourself; that is always available:

```bash
uat catalog
uat install --project . --agent claude-code --add go postgresql
```

### There is no pack for my technology

There are ~410 vendored rule documents with no curated pack. Search them:

```bash
uat catalog --search wordpress
uat add-rule awesome-copilot:wordpress --project .
```

If nothing matches, write a pack — see
[Packs & profiles](PACKS.md#writing-a-pack).

---

## MCP problems

### The server is in `.agent-toolkit/mcp/` but my tool does not see it

Check whether your tool's MCP scope is global:

```bash
uat agents --show <id>
```

For a global-scope tool the toolkit does **not** write to your home directory
during an install. It writes a neutral spec and tells you what to paste
where. `.agent-toolkit/mcp/README.md` has the per-server status and the
manual step.

### Figma skills are missing

They are deliberately not vendored — Figma's skills are governed by the Figma
Developer Terms rather than an open-source licence. The `mcp-figma` pack
ships an integration guide and tells you how to install Figma's official
skills from source. See
[Third-party notices](../THIRD_PARTY_NOTICES.md#not-vendored).

---

## Toolkit repository problems

### `uat vendor verify` fails

A snapshot no longer hashes to its pin, which means it was edited locally.
That is the check doing its job.

```bash
uat vendor sync --only <id> --force    # restore from the pinned commit
```

If the edit was intentional, it is in the wrong place. Move it to an overlay
pack in `catalog/packs/` or to `catalog/core/`. Content under `vendor/` is
never edited — see [Vendoring & provenance](VENDORING.md).

### `doctor` reports an undeclared vendor directory

Something was copied into `vendor/` by hand, so it has no provenance and is
invisible to `sync`, `verify` and every pack. Either register it or delete
it:

```bash
uat vendor add-local <path> --id <id> --license "<licence>"
```

### `doctor` reports a missing vendor path

A pack's `vendor_maps` points at a file that is not in the snapshot —
normally a typo in a `from` path, or an upstream that renamed a file after a
`ref` bump. Fix the pack, or pin back.

### Tests fail after my change

```bash
./bin/uat-test        # 151 tests
./bin/uat doctor
./bin/uat install --project /tmp/probe --agent claude-code --yes --dry-run
```

All three are required before claiming a change to this repository is
complete. See [`AGENTS.md`](../AGENTS.md).

---

## Still stuck

Collect this before reporting:

```bash
uat --verbose status  --project .
uat detect  --project .
uat agents  --show <your-agent-id>
uat doctor
```

`--verbose` makes the change report list unchanged files too, which is
usually where the surprise is.
