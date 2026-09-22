# Toolkit Setup and Optional Ponytail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Ponytail explicitly opt-in and add a cross-platform `uat setup` command that copies the runnable toolkit into a per-user application directory and exposes its launcher on PATH.

**Architecture:** Keep pack selection declarative: Ponytail becomes an optional catalog pack and is removed from the core profile, while explicit pack/profile/all selections continue to resolve normally. Add a focused `src/uat/setup.py` module for platform destination calculation, runtime copying through existing report-aware filesystem helpers, Unix launcher/profile setup, and Windows PATH registration; keep `cli.py` responsible only for parsing, output, and dispatch.

**Tech Stack:** Python 3.9+ standard library, `argparse`, `pathlib`, existing `Report`/`copy_file`/`copy_tree` utilities, existing Windows registry helper, unittest test suite, Markdown documentation.

**Spec:** `docs/superpowers/specs/2026-09-22-setup-and-optional-ponytail-design.md`

## Global Constraints

- `vendor/` is never edited; Ponytail's upstream snapshot remains byte-for-byte unchanged.
- The installer never overwrites without `--force`; setup uses the same report-aware conflict behavior.
- The setup copy contains `src/`, `catalog/`, `vendor/`, optional `VERSION`/`LICENSE`, and both launchers when present; it excludes `.git/`, `tests/`, and `docs/`.
- Default setup destinations are `%LOCALAPPDATA%\\Universal-Agent-Toolkit` on Windows, `~/Library/Application Support/Universal-Agent-Toolkit` on macOS, and `~/.local/share/universal-agent-toolkit` on Linux/other Unix.
- Unix setup creates `~/.local/bin/uat` and an idempotent PATH block; Windows setup adds the copied app's `bin/` to the user PATH through the existing helper.
- Project installs continue to default to the current directory; documentation leads with `cd <project>` followed by `uat install --agent <id>`.
- Verification must include `./bin/uat-test`, `./bin/uat doctor`, and `./bin/uat install --project /tmp/probe --agent claude-code --yes --dry-run`.

---

### Task 1: Make Ponytail optional and lock down selection behavior

**Files:**
- Modify: `catalog/packs/ponytail/pack.json`
- Modify: `catalog/profiles/core.json`
- Test: `tests/test_uat.py` in `TestPonytail`
- Modify: `docs/PACKS.md`

**Interfaces:**
- Consumes: `Catalog.recommend()`, `Catalog.resolve_profile()`, and existing pack installation behavior.
- Produces: a catalog where `ponytail` is optional, absent from `core`, but still installable by explicit pack selection.

- [ ] **Step 1: Replace the outdated default-selection test with failing assertions**

Update `TestPonytail.test_ponytail_is_selected_by_default_but_can_be_omitted` to assert the new contract:

```python
def test_ponytail_is_not_recommended_by_default(self):
    self.assertNotIn("ponytail", self.catalog.recommend(set()))
    self.assertNotIn("ponytail", self.catalog.resolve_profile("core"))

def test_ponytail_can_still_be_selected_explicitly(self):
    self.assertIn("ponytail", self.catalog.expand({"ponytail"}))
```

- [ ] **Step 2: Run the focused tests and verify the expected failure**

Run:

```bash
python3 -m unittest tests.test_uat.TestPonytail -v
```

Expected: the first assertion fails because the pack is currently core and the core profile still lists it.

- [ ] **Step 3: Make the minimal catalog changes**

In `catalog/packs/ponytail/pack.json`, change only:

```json
"tier": "optional"
```

In `catalog/profiles/core.json`, remove only the `"ponytail",` entry. Do not alter the pack's vendor maps or `vendor/ponytail/`.

- [ ] **Step 4: Run the focused tests and verify green**

Run:

```bash
python3 -m unittest tests.test_uat.TestPonytail -v
```

Expected: all Ponytail tests pass, including the existing explicit installation test.

- [ ] **Step 5: Update pack documentation and commit**

Change `docs/PACKS.md` so the core list excludes Ponytail, the optional tier explains that Ponytail is opt-in, and the profile count/pack examples no longer claim Ponytail is core. Keep the explicit selection examples. Then run:

```bash
git add catalog/packs/ponytail/pack.json catalog/profiles/core.json tests/test_uat.py docs/PACKS.md
git commit -m "feat: make ponytail an opt-in pack"
```

### Task 2: Add platform destination and runtime-copy primitives

**Files:**
- Create: `src/uat/setup.py`
- Test: `tests/test_uat.py` in a new `TestSetup` class

**Interfaces:**
- Consumes: `Report`, `copy_file`, `copy_tree`, `ToolkitError`, `Path`, `os`, and the existing `windows.add_to_user_path` integration point.
- Produces:
  - `SetupPaths` dataclass with `app_dir`, `bin_dir`, `launcher`, and optional `profile` fields.
  - `platform_paths(platform: str, home: Path, env: dict[str, str]) -> SetupPaths`.
  - `copy_runtime(source: Path, destination: Path, *, force: bool, report: Report) -> None`.
  - `setup_toolkit(source: Path, *, platform: str | None = None, home: Path | None = None, env: dict[str, str] | None = None, force: bool = False, dry_run: bool = False, profile_override: Path | None = None) -> SetupResult`.

- [ ] **Step 1: Write failing platform-path tests**

Import the new module in `tests/test_uat.py` with `from uat import setup`, and define the disposable fixture used by all setup tests:

```python
class TestSetup(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="uat-setup-test-"))
        self.source = self.tmp / "source"
        self.home = self.tmp / "home"
        self.source.mkdir()
        self.home.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
```

Add tests with temporary homes and explicit platform names:

```python
def test_platform_paths_use_documented_app_directories(self):
    home = Path("/tmp/uat-home")
    self.assertEqual(
        setup.platform_paths("win32", home, {"LOCALAPPDATA": "/tmp/local"}).app_dir,
        Path("/tmp/local/Universal-Agent-Toolkit"),
    )
    self.assertEqual(
        setup.platform_paths("darwin", home, {}).app_dir,
        home / "Library/Application Support/Universal-Agent-Toolkit",
    )
    self.assertEqual(
        setup.platform_paths("linux", home, {}).app_dir,
        home / ".local/share/universal-agent-toolkit",
    )

def test_platform_paths_reject_missing_windows_local_app_data(self):
    with self.assertRaises(ToolkitError):
        setup.platform_paths("win32", Path("/tmp/uat-home"), {})
```

- [ ] **Step 2: Run the path tests to verify they fail for the missing module**

Run:

```bash
python3 -m unittest tests.test_uat.TestSetup.test_platform_paths_use_documented_app_directories tests.test_uat.TestSetup.test_platform_paths_reject_missing_windows_local_app_data -v
```

Expected: import or attribute failure because `uat.setup` and `platform_paths` do not yet exist.

- [ ] **Step 3: Implement `SetupPaths`, `platform_paths`, and runtime copying**

Use `sys.platform`-compatible values (`win32`, `darwin`, and all other values as Unix). Resolve Windows app data from `LOCALAPPDATA`, and raise `ToolkitError` if it is absent. Use the exact runtime list from the spec. For directories, call `copy_tree`; for optional files and launchers, call `copy_file`. The `bin/uat` file must remain executable after copying when the destination is real, matching the source mode.

Use a `SetupResult` dataclass to return the resolved paths, report, and any human-readable next-step notes needed by `cmd_setup`.

- [ ] **Step 4: Add runtime-copy tests and verify green**

Extend the `TestSetup` fixture's `self.source` with `src/uat/cli.py`, `catalog/agents.json`, `vendor/example/SOURCE.json`, `VERSION`, `LICENSE`, both launchers, plus `tests/`, `docs/`, and `.git/` sentinel files. Assert runtime files are copied, excluded directories are absent, and `dry_run=True` leaves the destination absent. Assert a second identical copy reports no overwrite/conflict actions.

Run:

```bash
python3 -m unittest tests.test_uat.TestSetup -v
```

Expected: path and copy tests pass; PATH/profile tests added in Task 3 may remain pending.

- [ ] **Step 5: Commit the setup primitives**

```bash
git add src/uat/setup.py tests/test_uat.py
git commit -m "feat: add platform-aware toolkit setup primitives"
```

### Task 3: Add Unix launcher/profile setup and CLI dispatch

**Files:**
- Modify: `src/uat/setup.py`
- Modify: `src/uat/cli.py`
- Test: `tests/test_uat.py` in `TestSetup` and a parser/CLI test class if needed

**Interfaces:**
- Consumes: `SetupPaths`, `setup_toolkit`, `Report`, and `windows.add_to_user_path`.
- Produces: `cmd_setup(args) -> int`, parser support for `uat setup [--dry-run] [--force]`, and working platform registration after the runtime copy.

- [ ] **Step 1: Write failing Unix registration tests**

Add tests that patch the setup module's home/platform inputs and use temporary profile files:

```python
def test_unix_setup_creates_launcher_and_idempotent_profile_block(self):
    profile = self.tmp / ".profile"
    profile.write_text("export OTHER=value\n", encoding="utf-8")
    result = setup.setup_toolkit(
        self.source, platform="linux", home=self.home,
        env={"SHELL": "/bin/bash"}, profile_override=profile,
    )
    self.assertTrue((self.home / ".local/bin/uat").is_symlink())
    first = profile.read_text(encoding="utf-8")
    setup.setup_toolkit(
        self.source, platform="linux", home=self.home,
        env={"SHELL": "/bin/bash"}, profile_override=profile,
    )
    self.assertEqual(profile.read_text(encoding="utf-8"), first)
    self.assertIn(".local/bin", first)

def test_unix_setup_dry_run_does_not_write_launcher_or_profile(self):
    profile = self.tmp / ".profile"
    result = setup.setup_toolkit(
        self.source, platform="darwin", home=self.home,
        env={"SHELL": "/bin/zsh"}, profile_override=profile, dry_run=True,
    )
    self.assertFalse((self.home / ".local/bin/uat").exists())
    self.assertFalse(profile.exists())
```

`profile_override` is a test-only keyword accepted by the implementation so tests never write a real user profile; the CLI leaves it unset.

- [ ] **Step 2: Run the Unix registration tests and verify red**

Run:

```bash
python3 -m unittest tests.test_uat.TestSetup.test_unix_setup_creates_launcher_and_idempotent_profile_block tests.test_uat.TestSetup.test_unix_setup_dry_run_does_not_write_launcher_or_profile -v
```

Expected: failure because Unix registration and the setup command do not exist.

- [ ] **Step 3: Implement Unix registration**

Create `~/.local/bin` as needed, create `uat` as a symlink to the copied app launcher, and report a conflict for an existing unrelated launcher unless `force=True`. Add a stable marked block to the selected profile, preserving all existing text. Choose `~/.zprofile` for zsh and `~/.profile` otherwise; use the test override when supplied. The block must be inserted once and contain an export that prepends `~/.local/bin`.

Do not attempt to mutate the parent shell. Return a note telling the user to start a new shell and, for dry-run output, identify the profile that would change.

- [ ] **Step 4: Write failing Windows and parser tests**

Import `from uat import cli` alongside the setup import. Add tests that patch setup inputs and assert the existing Windows helper receives the copied app bin path, plus parser assertions:

```python
def test_windows_setup_registers_copied_bin(self):
    with patch("uat.setup.add_to_user_path") as add:
        setup.setup_toolkit(
            self.source, platform="win32", home=self.home,
            env={"LOCALAPPDATA": str(self.tmp / "local")},
        )
    add.assert_called_once_with(str(self.tmp / "local/Universal-Agent-Toolkit/bin"))

def test_parser_exposes_setup_flags(self):
    args = cli.build_parser().parse_args(["setup", "--dry-run", "--force"])
    self.assertEqual(args.cmd, "setup")
    self.assertTrue(args.dry_run)
    self.assertTrue(args.force)
```

- [ ] **Step 5: Run the new tests to verify the expected failure**

Run:

```bash
python3 -m unittest tests.test_uat.TestSetup -v
```

Expected: Windows registration and parser assertions fail until CLI wiring is added.

- [ ] **Step 6: Implement `cmd_setup` and parser wiring**

Import the setup module in `cli.py`, add `cmd_setup(args)` near the other top-level commands, and add:

```python
s = sub.add_parser("setup", help="copy the toolkit to its per-user location and set up PATH")
s.add_argument("--dry-run", action="store_true", help="show setup changes without writing")
s.add_argument("--force", action="store_true", help="replace conflicting setup files")
s.set_defaults(func=cmd_setup)
```

`cmd_setup` must print the source, destination, platform, report, and next-step PATH message; return nonzero only through normal `ToolkitError` handling or an unsuccessful setup result. Ensure setup validates the source runtime before copying and calls Windows registration only after the copy plan succeeds.

- [ ] **Step 7: Run the complete focused setup tests and commit**

Run:

```bash
python3 -m unittest tests.test_uat.TestSetup -v
python3 -m unittest tests.test_uat.TestWindowsPath -v
```

Expected: all setup and existing Windows PATH tests pass.

```bash
git add src/uat/setup.py src/uat/cli.py tests/test_uat.py
git commit -m "feat: add uat setup command"
```

### Task 4: Rewrite the primary setup documentation around project-local install

**Files:**
- Modify: `README.md`
- Modify: `docs/GETTING-STARTED.md`
- Modify: `docs/CLI.md`
- Modify: `docs/PACKS.md`

**Interfaces:**
- Consumes: the shipped `uat setup` command and current-directory default for `install`.
- Produces: consistent onboarding instructions that start with platform setup and then run install from inside the project.

- [ ] **Step 1: Update README quick start**

Make the first Windows and macOS/Linux examples clone the toolkit, run `./bin/uat setup` or `./bin/uat.cmd setup`, then change into the target project and run `uat install --agent claude-code`. Keep `--project` examples only where they demonstrate automation or multi-project use. Change the progressive picker sample so Ponytail is shown unchecked/optional and retain the all/none/reset controls.

- [ ] **Step 2: Update getting started**

Restructure `docs/GETTING-STARTED.md` so OS setup is the first operational path. Document the three setup destinations, the shell restart/current-shell note, `--dry-run`, and `--force`. Make the install section use:

```bash
cd ~/code/my-app
uat install --agent claude-code
```

State that `--project PATH` defaults to `.` and remains useful from elsewhere. Remove or demote old instructions that manually symlink the source checkout as the primary setup.

- [ ] **Step 3: Update CLI reference**

Add `setup` to the command table and create a `uat setup` section with flags, platform destinations, conflict behavior, dry-run behavior, and examples. Update the `install` section's first examples and explain that the project option defaults to the current directory.

- [ ] **Step 4: Update pack documentation**

Change `docs/PACKS.md` tier counts/list and selection prose so Ponytail is optional and explicit selection examples remain visible. Reconcile profile counts with the actual catalog rather than leaving the old core count.

- [ ] **Step 5: Run documentation consistency searches and commit**

Run:

```bash
rg -n "Core.*ponytail|ponytail.*core|symlink.*checkout|uat install --project ~/code/my-app|five packs|core tier" README.md docs
git diff --check
```

Fix every stale user-facing statement found by the search, then commit:

```bash
git add README.md docs/GETTING-STARTED.md docs/CLI.md docs/PACKS.md
git commit -m "docs: lead with platform setup and project-local install"
```

### Task 5: Run full verification and inspect the final diff

**Files:**
- Verify: all changed files and committed history

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: evidence that selection behavior, setup behavior, docs, catalog integrity, and the required install dry run all work together.

- [ ] **Step 1: Run the focused regression groups**

```bash
python3 -m unittest tests.test_uat.TestPonytail tests.test_uat.TestSetup tests.test_uat.TestWindowsPath -v
```

Expected: zero failures or errors.

- [ ] **Step 2: Run the full repository test suite**

```bash
./bin/uat-test
```

Expected: exit code 0 and all tests passing.

- [ ] **Step 3: Run catalog/vendor integrity checks**

```bash
./bin/uat doctor
```

Expected: registry, catalog, all vendor hashes, and reachability checks pass with final status `healthy`.

- [ ] **Step 4: Run the required non-mutating install probe**

```bash
./bin/uat install --project /tmp/probe --agent claude-code --yes --dry-run
```

Expected: a dry-run install plan that does not write to `/tmp/probe` and does not include Ponytail in the default pack list.

- [ ] **Step 5: Inspect the final diff and status**

```bash
git diff --check HEAD~5..HEAD
git status --short
git log --oneline -6
```

Confirm there are no edits under `vendor/`, no generated temporary project files in the repository, and all commits use conventional messages without AI attribution. Report any pre-existing unrelated worktree changes separately.
