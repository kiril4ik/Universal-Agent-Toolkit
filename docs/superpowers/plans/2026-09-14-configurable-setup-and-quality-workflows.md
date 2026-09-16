# Configurable Setup and Quality Workflows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a progressive, fully scriptable installer; default-deselectable Ponytail; configurable downstream quality policies; and the serious installer repairs identified in the audit.

**Architecture:** Extend `InstallPlan` with persisted policy fields, keep packs as the content unit, and make the existing picker capability-group aware. Reconcile the previous ownership manifest against each replacement plan so removals remain safe and previewable. Keep downstream behaviors as concise installed policy rather than database- or framework-specific executable code.

**Tech Stack:** Python 3.9+ standard library, JSON pack catalog, Markdown policy/workflow files, Bash validation, unittest suite, pinned Git vendor snapshots, built-in image generation.

**Spec:** `docs/superpowers/specs/2026-09-14-configurable-setup-and-quality-workflows-design.md`

## Global Constraints

- Never edit bytes under `vendor/`; generate Ponytail only through `uat vendor sync` at an exact commit.
- Existing target-project files are preserved unless `--force` was explicitly supplied.
- Ponytail is selected by default but remains deselectable and bypassable by an exact `--packs` list.
- Planning can be completely absent; generated adapters must not point at absent workflow files.
- Every interactive answer has a non-interactive flag.
- Database dumps and screenshots are downstream project policies, not operations performed against this toolkit repository.
- Use only the Python standard library in `src/uat/`.

---

### Task 1: Repair audit defects and argument semantics

**Files:**
- Modify: `tests/test_uat.py`
- Modify: `src/uat/embed.py`
- Modify: `src/uat/cli.py`
- Modify: `src/uat/install.py`

**Interfaces:**
- Produces: portable `EMBEDDED.json`, `_validate_install_args(args)`, explicit empty-pack semantics, and embedded dry-run reporting.

- [ ] **Step 1: Write failing regression tests**

Add tests asserting:

```python
def test_embedded_marker_does_not_leak_source_checkout(self):
    dest = self.embed()
    self.assertNotIn(str(ROOT), (dest / "EMBEDDED.json").read_text())

def test_explicit_empty_pack_list_stays_empty(self):
    plan = inst.build_plan(
        ROOT, self.project, registry=self.registry, catalog=self.catalog,
        agent_keys=["claude-code"], mode="focused", explicit_packs=[])
    self.assertEqual(plan.pack_ids, [])

def test_with_vendor_requires_embed(self):
    self.assertEqual(main(["install", "--project", str(self.project),
                           "--agent", "claude-code", "--with-vendor", "--yes"]), 1)

def test_embed_dry_run_previews_embedded_launcher(self):
    result = subprocess.run(
        [str(ROOT / "bin/uat"), "install", "--project", str(self.project),
         "--agent", "claude-code", "--embed", "--dry-run"],
        capture_output=True, text=True, check=False)
    out = result.stdout + result.stderr
    self.assertIn(".agent-toolkit/toolkit/uat", out)
    self.assertFalse((self.project / ".agent-toolkit").exists())
```

- [ ] **Step 2: Run the focused tests and confirm they fail**

Run: `./bin/uat-test TestEmbedding TestInstallArgumentSemantics`

- [ ] **Step 3: Implement the minimum repairs**

Remove the absolute `source` value from embedded metadata. Distinguish
`explicit_packs is not None` from truthiness in `build_plan()` and selection.
Reject `--with-vendor` without `--embed`. For embedded dry runs, pass a dry-run
`Report` into `embedlib.embed()` before previewing the main install.

- [ ] **Step 4: Run focused and full tests**

Run: `./bin/uat-test TestEmbedding TestInstallArgumentSemantics && ./bin/uat-test`

- [ ] **Step 5: Commit**

```bash
git add tests/test_uat.py src/uat/embed.py src/uat/cli.py src/uat/install.py
git commit -m "fix: make install previews and arguments truthful"
```

### Task 2: Add the progressive setup policy model

**Files:**
- Modify: `tests/test_uat.py`
- Modify: `src/uat/install.py`
- Modify: `src/uat/cli.py`
- Modify: `src/uat/render.py`
- Modify: `docs/CLI.md`
- Modify: `docs/GETTING-STARTED.md`

**Interfaces:**
- Produces: `InstallPolicy`, `PROJECT_KINDS`, `PLANNING_MODES`,
  `TECHNOLOGY_ADDITION_MODES`, `ACCEPTANCE_MODES`, `DB_BACKUP_MODES`, and
  `IMAGE_GENERATION_MODES`.
- Consumes: existing `InstallPlan`, CLI parser, and `project.json` state.

- [ ] **Step 1: Add failing model and parser tests**

Test all accepted values, defaults for frontend/non-frontend projects,
round-tripping through `project.json`, preserving answers during additive
reinstall, and parser availability of:

```text
--project-kind
--planning
--technology-additions
--acceptance
--visual-validation / --no-visual-validation
--db-backups
--image-generation
```

- [ ] **Step 2: Confirm the focused tests fail**

Run: `./bin/uat-test TestInstallPolicy`

- [ ] **Step 3: Implement the policy value object and persistence**

Use a frozen dataclass:

```python
@dataclass(frozen=True)
class InstallPolicy:
    project_kind: str
    planning: str
    technology_additions: str
    acceptance: str
    visual_validation: bool
    db_backups: str
    image_generation: str
```

Add `policy: InstallPolicy` to `InstallPlan`. Resolve `auto` project kind before
writing `project.json`. Preserve recorded values on additive reinstall.

- [ ] **Step 4: Add the progressive prompts**

Allow omitted `--agent` only for a terminal-driven install and prompt for one
or more agent IDs. Add short, sequential prompts for project kind, interaction
mode, planning, and the five automation policies. `--yes` remains strictly
non-interactive and requires `--agent`.

- [ ] **Step 5: Render and document active policy**

Summarize policy choices in `CORE.md`, without inlining the policy bodies.
Document interactive and silent equivalents.

- [ ] **Step 6: Verify**

Run: `./bin/uat-test TestInstallPolicy TestInstallInteraction && ./bin/uat-test`

- [ ] **Step 7: Commit**

```bash
git add tests/test_uat.py src/uat/install.py src/uat/cli.py src/uat/render.py docs/CLI.md docs/GETTING-STARTED.md
git commit -m "feat(cli): add progressive setup policies"
```

### Task 3: Make planning optional and remove duplicated phase numbering

**Files:**
- Modify: `tests/test_uat.py`
- Modify: `src/uat/install.py`
- Modify: `src/uat/cli.py`
- Modify: `src/uat/render.py`
- Modify: `catalog/workflow/README.md`
- Modify: `catalog/workflow/00-triage.md`
- Modify: `catalog/workflow/05-rules.md`
- Modify: `docs/WORKFLOW.md`

**Interfaces:**
- Consumes: `InstallPlan.policy.planning`.
- Produces: workflow-free installs and name-based generated workflow guidance.

- [ ] **Step 1: Write failing workflow-absence tests**

Assert `planning=off` omits `workflow/`, `reports/`, `START-HERE.md`, and slash
commands; adapters and `CORE.md` remain valid; `uat workflow` reports that the
workflow is disabled. Add string assertions preventing stale phrases such as
“phase 06 settles the stack” in generated files.

- [ ] **Step 2: Confirm failure**

Run: `./bin/uat-test TestOptionalWorkflow TestWorkflowTrigger`

- [ ] **Step 3: Gate workflow generation on policy**

Copy workflow/report files and render planning commands only for `adaptive` or
`full`. Remove stale workflow-owned files when switching off through the safe
reconciliation implemented in Task 7.

- [ ] **Step 4: Replace prose phase numbers with names**

Keep numbered filenames for ordering, but refer to “stack”, “rules”, “gate”,
and “acceptance” in generated summaries. Update the workflow precedence and
triage text to honor `adaptive` versus `full`.

- [ ] **Step 5: Verify and commit**

Run: `./bin/uat-test TestOptionalWorkflow TestWorkflowTrigger TestSkillPrecedence`

```bash
git add tests/test_uat.py src/uat/install.py src/uat/cli.py src/uat/render.py catalog/workflow docs/WORKFLOW.md
git commit -m "feat(workflow): make project planning optional"
```

### Task 4: Group capabilities and make confirmation exact

**Files:**
- Modify: `tests/test_uat.py`
- Modify: `src/uat/catalog.py`
- Modify: `src/uat/picker.py`
- Modify: `src/uat/install.py`
- Modify: `src/uat/cli.py`
- Modify: selected `catalog/packs/*/pack.json`
- Modify: `docs/PACKS.md`

**Interfaces:**
- Produces: `Pack.category`, `InstallContents`, `describe_plan_contents()`, and
  `uat detect --recommend`.

- [ ] **Step 1: Write failing catalog/output tests**

Test the six ordered categories, default fallback to `technology`, category
headings in the keyboard picker, exact rule/skill/MCP names in the install
plan, and detection recommendations showing evidence and contributed content.

- [ ] **Step 2: Confirm failure**

Run: `./bin/uat-test TestCatalogCategories TestInstallSummary TestDetectRecommendations`

- [ ] **Step 3: Add category metadata and grouping**

Support `engineering`, `technology`, `browser-quality`, `design-content`,
`infrastructure`, and `integrations`. Add explicit category fields only where
the default `technology` category is incorrect.

- [ ] **Step 4: Centralize content prediction**

Extend the existing pack-output prediction so real installs and dry runs share
one exact inventory of rules, skills, MCP servers, hooks, and other top-level
content. Print that inventory before `Proceed?`.

- [ ] **Step 5: Implement `uat detect --recommend`**

For each detected token, show evidence, matching packs, and content. Show
default-selected packs separately and do not mutate the project.

- [ ] **Step 6: Verify and commit**

Run: `./bin/uat-test TestCatalogCategories TestKeyboardPicker TestInstallSummary TestDetectRecommendations`

```bash
git add tests/test_uat.py src/uat/catalog.py src/uat/picker.py src/uat/install.py src/uat/cli.py catalog/packs docs/PACKS.md
git commit -m "feat(cli): group and explain install capabilities"
```

### Task 5: Vendor and install Ponytail by default

**Files:**
- Modify: `catalog/vendor.json`
- Create: `vendor/ponytail/**` through `uat vendor sync`
- Create: `catalog/packs/ponytail/pack.json`
- Modify: `catalog/profiles/core.json`
- Modify: `tests/test_uat.py`
- Modify: `THIRD_PARTY_NOTICES.md`
- Modify: `README.md`
- Modify: `docs/VENDORING.md`
- Modify: `docs/PACKS.md`

**Interfaces:**
- Produces: core-tier `ponytail` pack mapping `AGENTS.md` to
  `rules/PONYTAIL.md` and `skills/` to `skills/`.

- [ ] **Step 1: Add failing reachability/default tests**

Assert Ponytail is recommended with no detected stack, can be removed by the
picker, is absent from an explicit pack list that omits it, installs the rule
and all six skills, and carries verified provenance.

- [ ] **Step 2: Confirm failure**

Run: `./bin/uat-test TestPonytail`

- [ ] **Step 3: Register the exact upstream pin**

Pin `https://github.com/DietrichGebert/ponytail.git` at
`e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156`, MIT, including only
`AGENTS.md`, `skills`, `LICENSE`, and `README.md`.

- [ ] **Step 4: Fetch through the vendor command**

Run: `uat vendor sync --only ponytail`

Do not modify the resulting snapshot.

- [ ] **Step 5: Add the pack and notices**

Set `tier` to `core`, `category` to `engineering`, and document that core is a
default rather than a mandatory tier. Change picker copy from `always` to
`default`.

- [ ] **Step 6: Verify and commit**

Run: `uat doctor && ./bin/uat-test TestPonytail TestVendorReachability`

```bash
git add catalog/vendor.json vendor/ponytail catalog/packs/ponytail catalog/profiles/core.json tests/test_uat.py THIRD_PARTY_NOTICES.md README.md docs/VENDORING.md docs/PACKS.md
git commit -m "feat(skills): install Ponytail by default"
```

### Task 6: Add downstream quality policies

**Files:**
- Modify: `tests/test_uat.py`
- Modify: `catalog/core/SAFETY.md`
- Modify: `catalog/core/VERIFICATION.md`
- Modify: `catalog/workflow/03-screens-and-flows.md`
- Modify: `catalog/workflow/05-rules.md`
- Modify: `catalog/workflow/08-design.md`
- Modify: `catalog/workflow/13-acceptance.md`
- Create: `catalog/packs/codex-image-generation/pack.json`
- Create: `catalog/packs/codex-image-generation/files/rules/CODEX_IMAGE_GENERATION.md`
- Modify: `catalog/profiles/design.json`
- Modify: `README.md`
- Modify: `docs/CORE-POLICY.md`
- Modify: `docs/WORKFLOW.md`

**Interfaces:**
- Consumes: persisted install policies.
- Produces: conditional database completion dumps, Playwright story/viewport
  checks, screenshot evidence, optional technology additions, and Codex image
  generation guidance.

- [ ] **Step 1: Add failing policy-content tests**

Assert exact policy keys and required language: `backups/db/`, persistent test
database handling, disposable-test exemption, all journeys, the three default
viewports, all documented pages/states, screenshot limitations, technology
addition modes, `codex --version`, a response probe, `$imagegen`, project-local
destinations, and non-destructive replacement.

- [ ] **Step 2: Confirm failure**

Run: `./bin/uat-test TestConfigurableQualityPolicies`

- [ ] **Step 3: Update core and workflow policy**

Keep behavior conditional on `project.json`; do not introduce generic dump
scripts that guess database engines or credentials. Require honest NOT VERIFIED
reporting whenever a browser journey, screenshot state, or dump cannot run.

- [ ] **Step 4: Add the Codex image pack**

Author the rule under `catalog/packs/`, make it recommended for `frontend`, and
include it in the design profile. Do not put Codex-specific paths in Python.

- [ ] **Step 5: Verify and commit**

Run: `./bin/uat-test TestConfigurableQualityPolicies TestProductAcceptance && uat doctor`

```bash
git add tests/test_uat.py catalog/core catalog/workflow catalog/packs/codex-image-generation catalog/profiles/design.json README.md docs/CORE-POLICY.md docs/WORKFLOW.md
git commit -m "feat(policy): configure acceptance backups and image generation"
```

### Task 7: Reconcile replacement installs safely

**Files:**
- Modify: `tests/test_uat.py`
- Modify: `src/uat/install.py`
- Modify: `src/uat/cli.py`
- Modify: `docs/CLI.md`
- Modify: `docs/ARCHITECTURE.md`

**Interfaces:**
- Produces: `desired_toolkit_files(plan, toolkit_root)`,
  `reconcile_install(plan, toolkit_root, report)`, and safe removed-agent
  surface cleanup.
- Consumes: previous `installed.json` hashes and agent registry metadata.
- Extends: `execute(..., replace: bool = False)` so reconciliation is explicit
  and never inferred from an empty selection.

- [ ] **Step 1: Write failing reconciliation tests**

Cover four cases:

```python
def test_replace_removes_unchanged_files_from_dropped_pack(self):
    self.install(["claude-code"], packs=["go"])
    dropped = self.project / ".agent-toolkit/rules/GO.md"
    replacement = inst.build_plan(
        ROOT, self.project, registry=self.registry, catalog=self.catalog,
        agent_keys=["claude-code"], mode="focused", explicit_packs=[])
    inst.execute(replacement, ROOT, replace=True)
    self.assertFalse(dropped.exists())

def test_replace_preserves_modified_file_from_dropped_pack(self):
    self.install(["claude-code"], packs=["go"])
    dropped = self.project / ".agent-toolkit/rules/GO.md"
    dropped.write_text(dropped.read_text() + "\nlocal rule\n")
    replacement = inst.build_plan(
        ROOT, self.project, registry=self.registry, catalog=self.catalog,
        agent_keys=["claude-code"], mode="focused", explicit_packs=[])
    result = inst.execute(replacement, ROOT, replace=True)
    self.assertTrue(dropped.exists())
    self.assertTrue(result.report.conflicts())

def test_replace_removes_surfaces_for_dropped_agent(self):
    initial = inst.build_plan(
        ROOT, self.project, registry=self.registry, catalog=self.catalog,
        agent_keys=["claude-code", "cursor"], mode="focused", explicit_packs=[])
    inst.execute(initial, ROOT)
    replacement = inst.build_plan(
        ROOT, self.project, registry=self.registry, catalog=self.catalog,
        agent_keys=["claude-code"], mode="focused", explicit_packs=[])
    inst.execute(replacement, ROOT, replace=True)
    self.assertFalse((self.project / ".cursor/rules/00-agent-toolkit.mdc").exists())

def test_replace_dry_run_reports_removals_without_writing(self):
    self.install(["claude-code"], packs=["go"])
    dropped = self.project / ".agent-toolkit/rules/GO.md"
    replacement = inst.build_plan(
        ROOT, self.project, registry=self.registry, catalog=self.catalog,
        agent_keys=["claude-code"], mode="focused", explicit_packs=[])
    result = inst.execute(replacement, ROOT, replace=True, dry_run=True)
    self.assertTrue(dropped.exists())
    self.assertTrue(any(a.path.endswith("GO.md") for a in result.report.actions))
```

Also test removed MCP entries and hooks are removed from shared JSON while
foreign entries survive.

- [ ] **Step 2: Confirm failure**

Run: `./bin/uat-test TestReplacementReconciliation`

- [ ] **Step 3: Compute the desired manifest before rendering**

Enumerate core files, optional workflow files, exact pack files/vendor maps,
generated router/state files, selected agent surfaces, and MCP/hook entries.
Exclude embedded toolkit content from pack reconciliation.

- [ ] **Step 4: Remove only unchanged owned stale paths**

Use recorded hashes for files and recorded ownership for symlinks. Preserve
modified and unowned paths as conflicts. Apply the same action recording in
dry-run. Prune empty directories without crossing the project root.

- [ ] **Step 5: Reconcile shared and dropped-agent surfaces**

Reuse the existing surgical hook/MCP removal helpers. Remove only entries and
files attributed to the toolkit, then render current agents from the new plan.

- [ ] **Step 6: Verify and commit**

Run: `./bin/uat-test TestReplacementReconciliation TestUninstall TestMcp TestSessionHook && ./bin/uat-test`

```bash
git add tests/test_uat.py src/uat/install.py src/uat/cli.py docs/CLI.md docs/ARCHITECTURE.md
git commit -m "fix(install): reconcile removed packs and agents"
```

### Task 8: Regenerate the README flow diagram

**Files:**
- Replace: `docs/assets/simple-scheme.png`
- Modify: `README.md`

**Interfaces:**
- Produces: one project-bound PNG showing the progressive setup and optional
  planning branch.

- [ ] **Step 1: Generate the replacement with the built-in image tool**

Use this normalized prompt:

```text
Use case: infographic-diagram
Asset type: README installation and usage flow
Primary request: a clean dark technical flowchart for Universal Agent Toolkit
showing Select project type and agents -> Configure workflow and policies ->
Choose capabilities -> Review exact install. Then branch: Planning enabled ->
Plan work -> Implement; Planning skipped -> Implement. Finish with Verify user
stories and layouts -> Back up database when configured.
Style/medium: crisp documentation infographic, dark navy background, blue
connectors, green verification ending
Composition/framing: wide 16:9, generous spacing, readable at README width
Constraints: exact short labels, no logos, no decorative characters, no
watermark, no misspellings, no clipped text
```

- [ ] **Step 2: Inspect at original resolution**

Verify labels, branch directions, spacing, and absence of clipped or invented
content. Iterate once with a targeted correction if necessary.

- [ ] **Step 3: Link it from README**

Place it near Quick start with descriptive alt text and a short caption saying
planning is optional.

- [ ] **Step 4: Commit**

```bash
git add docs/assets/simple-scheme.png README.md
git commit -m "docs: illustrate configurable toolkit workflow"
```

### Task 9: Final audit and release verification

**Files:**
- Inspect: all changed files and repository status. A newly proven defect returns
  to the task that owns it and receives a regression test before its fix.

**Interfaces:**
- Consumes: all previous tasks.
- Produces: verified clean branch with no serious known regression.

- [ ] **Step 1: Run static checks**

```bash
python3 -m compileall -q src tests
find catalog/packs -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n
git diff --check main...HEAD
```

- [ ] **Step 2: Run complete repository checks**

```bash
./bin/uat-test
uat doctor
```

- [ ] **Step 3: Run required installation probe**

```bash
probe=$(mktemp -d)
uat install --project "$probe" --agent claude-code --yes --dry-run
```

Verify the output names Ponytail, policy defaults, exact skills/rules/tools,
and writes nothing to the probe.

- [ ] **Step 4: Inspect repository state**

Run: `git status --short --branch && git log --oneline --decorate -12`

Only the intended branch commits and no unexplained untracked files may remain.
