"""Test suite for the Universal Agent Toolkit.

Run:  python3 tests/test_uat.py
      ./bin/uat-test
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from uat import embed as embedlib          # noqa: E402
from uat import install as inst          # noqa: E402
from uat import vendorlib                 # noqa: E402
from uat.catalog import Catalog           # noqa: E402
from uat.detect import detect, looks_like_new_project   # noqa: E402
from uat.mcpconf import ServerSpec, shape_entry         # noqa: E402
from uat.registry import Registry         # noqa: E402
from uat.util import Report, ToolkitError, supports_symlinks  # noqa: E402


class TempProject(unittest.TestCase):
    """Base class providing a disposable project directory."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="uat-test-"))
        self.project = self.tmp / "project"
        self.project.mkdir()
        self.registry = Registry.load(ROOT)
        self.catalog = Catalog.load(ROOT)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel: str, content: str = "{}"):
        p = self.project / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def install(self, agents, packs=None, force=False, mode="focused"):
        plan = inst.build_plan(
            ROOT, self.project,
            registry=self.registry, catalog=self.catalog,
            agent_keys=agents, mode=mode,
            explicit_packs=packs or ["superpowers"],
        )
        return inst.execute(plan, ROOT, force=force)


# ----------------------------------------------------------------------
class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = Registry.load(ROOT)

    def test_loads_agents(self):
        self.assertGreater(len(self.registry), 5)
        self.assertIn("claude-code", self.registry.ids)

    def test_alias_resolution(self):
        self.assertEqual(self.registry.get("claude").id, "claude-code")

    def test_unknown_agent_is_an_error(self):
        with self.assertRaises(ToolkitError):
            self.registry.get("not-a-real-agent")

    def test_resolve_deduplicates(self):
        agents = self.registry.resolve(["claude-code", "claude", "cursor"])
        self.assertEqual([a.id for a in agents], ["claude-code", "cursor"])

    def test_only_claude_code_has_skills(self):
        with_skills = [a.id for a in self.registry if a.supports_skills]
        self.assertEqual(with_skills, ["claude-code"])

    def test_owned_paths_are_relative(self):
        for agent in self.registry:
            for p in agent.owned_paths():
                self.assertFalse(
                    Path(p).is_absolute(), f"{agent.id} has absolute path {p}"
                )

    def test_agents_declare_a_confidence(self):
        for agent in self.registry:
            self.assertIn(agent.confidence, ("high", "medium", "low"), agent.id)


# ----------------------------------------------------------------------
class TestCatalog(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog.load(ROOT)

    def test_loads_packs(self):
        self.assertGreater(len(self.catalog), 20)

    def test_every_pack_has_a_summary(self):
        for pack in self.catalog:
            self.assertTrue(pack.summary.strip(), f"{pack.id} has no summary")

    def test_requires_are_resolvable(self):
        self.catalog.validate()   # raises if not

    def test_expand_pulls_in_dependencies(self):
        pack = next((p for p in self.catalog if p.requires), None)
        if pack is None:
            self.skipTest("no pack declares requires")
        expanded = self.catalog.expand({pack.id})
        for dep in pack.requires:
            self.assertIn(dep, expanded)

    def test_recommend_always_includes_core(self):
        chosen = self.catalog.recommend(set())
        for pack in self.catalog.by_tier("core"):
            self.assertIn(pack.id, chosen)

    def test_recommend_reacts_to_detected_stack(self):
        without = self.catalog.recommend(set())
        with_go = self.catalog.recommend({"go"})
        self.assertIn("go", with_go)
        self.assertNotIn("go", without)

    def test_profiles_resolve(self):
        for name in self.catalog.profiles:
            ids = self.catalog.resolve_profile(name)
            self.assertTrue(ids, f"profile {name} is empty")

    def test_unknown_profile_is_an_error(self):
        with self.assertRaises(ToolkitError):
            self.catalog.resolve_profile("no-such-profile")


# ----------------------------------------------------------------------
class TestDetect(TempProject):
    def test_empty_project(self):
        self.assertTrue(looks_like_new_project(self.project))
        self.assertTrue(detect(self.project).is_empty_project())

    def test_detects_next_react_typescript(self):
        self.write("package.json", json.dumps(
            {"dependencies": {"next": "15", "react": "19"},
             "devDependencies": {"typescript": "5"}}))
        tokens = detect(self.project).tokens
        for expected in ("node", "nextjs", "react", "typescript", "frontend"):
            self.assertIn(expected, tokens)

    def test_detects_laravel(self):
        self.write("composer.json", json.dumps(
            {"require": {"laravel/framework": "^11"}}))
        tokens = detect(self.project).tokens
        self.assertIn("php", tokens)
        self.assertIn("laravel", tokens)

    def test_detects_infrastructure_from_compose(self):
        self.write("docker-compose.yml",
                   "services:\n  db:\n    image: postgres:16\n"
                   "  cache:\n    image: redis:7\n")
        tokens = detect(self.project).tokens
        self.assertIn("docker", tokens)
        self.assertIn("postgresql", tokens)
        self.assertIn("redis", tokens)

    def test_evidence_is_recorded(self):
        self.write("go.mod", "module example.com/x\n")
        d = detect(self.project)
        self.assertIn("go", d.tokens)
        self.assertIn("go.mod", d.why("go"))

    def test_malformed_package_json_does_not_crash(self):
        self.write("package.json", "{not valid json")
        self.assertIn("node", detect(self.project).tokens)


# ----------------------------------------------------------------------
class TestInstallScoping(TempProject):
    """The core promise: only the chosen agent's files are created."""

    def test_claude_code_does_not_create_cursor_files(self):
        self.install(["claude-code"])
        self.assertTrue((self.project / "CLAUDE.md").exists())
        self.assertTrue((self.project / ".agent-toolkit").is_dir())
        for forbidden in (".cursor", ".windsurf", ".clinerules", ".roo",
                          ".junie", "AGENTS.md", "GEMINI.md", ".github"):
            self.assertFalse(
                (self.project / forbidden).exists(),
                f"claude-code install leaked {forbidden}",
            )

    def test_cursor_does_not_create_claude_files(self):
        self.install(["cursor"])
        self.assertTrue((self.project / ".cursor/rules/00-agent-toolkit.mdc").exists())
        self.assertFalse((self.project / "CLAUDE.md").exists())
        self.assertFalse((self.project / ".claude").exists())

    def test_everything_lands_in_one_folder(self):
        self.install(["claude-code"])
        top = {p.name for p in self.project.iterdir()}
        expected = {".agent-toolkit", ".claude", ".mcp.json", "CLAUDE.md"}
        self.assertTrue(
            top.issubset(expected),
            f"unexpected top-level entries: {top - expected}",
        )

    def test_cursor_mdc_has_valid_frontmatter(self):
        self.install(["cursor"])
        text = (self.project / ".cursor/rules/00-agent-toolkit.mdc").read_text()
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("alwaysApply: true", text)

    def test_multi_agent_writes_agents_md_once(self):
        result = self.install(["cursor", "codex"])
        self.assertTrue((self.project / "AGENTS.md").exists())
        writes = [a for a in result.report.actions
                  if a.path.endswith("AGENTS.md") and a.kind == "add"]
        self.assertEqual(len(writes), 1, "AGENTS.md written more than once")


# ----------------------------------------------------------------------
class TestSkillMounting(TempProject):
    def test_skills_are_linked_not_duplicated(self):
        if not supports_symlinks(self.project):
            self.skipTest("filesystem does not support symlinks")
        self.install(["claude-code"])
        mount = self.project / ".claude/skills"
        self.assertTrue(mount.is_symlink())
        self.assertTrue((mount / "brainstorming/SKILL.md").exists())

    def test_copy_mode_materialises_files(self):
        plan = inst.build_plan(
            ROOT, self.project, registry=self.registry, catalog=self.catalog,
            agent_keys=["claude-code"], mode="focused",
            explicit_packs=["superpowers"], skills_mode="copy",
        )
        inst.execute(plan, ROOT)
        mount = self.project / ".claude/skills"
        self.assertFalse(mount.is_symlink())
        self.assertTrue((mount / "brainstorming/SKILL.md").is_file())


# ----------------------------------------------------------------------
class TestVendoredContentIsReal(TempProject):
    """Guards against the failure mode that motivated this rewrite."""

    def test_superpowers_skill_is_full_upstream_text(self):
        self.install(["claude-code"], packs=["superpowers"])
        skill = self.project / ".agent-toolkit/skills/brainstorming/SKILL.md"
        self.assertTrue(skill.exists())
        text = skill.read_text(encoding="utf-8")
        # A paraphrase loses the load-bearing parts. Check for them.
        self.assertGreater(len(text), 10_000, "brainstorming skill looks summarised")
        self.assertIn("HARD-GATE", text)
        self.assertIn("Red Flags", text)

    def test_vendor_snapshots_match_their_pins(self):
        for up in vendorlib.load_upstreams(ROOT):
            ok, detail = vendorlib.verify_one(up, ROOT)
            self.assertTrue(ok, f"{up.id}: {detail}")

    def test_every_vendor_map_target_exists(self):
        for pack in self.catalog:
            for vm in pack.vendor_maps:
                for rel in vm.required_paths():
                    self.assertTrue(
                        (ROOT / "vendor" / vm.vendor / rel).exists(),
                        f"pack {pack.id} points at missing {vm.vendor}/{rel}",
                    )


# ----------------------------------------------------------------------
class TestIdempotencyAndSafety(TempProject):
    def test_second_install_changes_nothing(self):
        self.install(["claude-code"])
        second = self.install(["claude-code"])
        self.assertEqual(second.report.counts().get("add", 0), 0)
        self.assertFalse(second.report.conflicts())

    def test_existing_user_file_is_never_clobbered(self):
        self.write("CLAUDE.md", "# my own instructions\n")
        result = self.install(["claude-code"])
        self.assertEqual(
            (self.project / "CLAUDE.md").read_text(), "# my own instructions\n"
        )
        self.assertTrue(result.report.conflicts())

    def test_force_replaces(self):
        self.write("CLAUDE.md", "# mine\n")
        self.install(["claude-code"], force=True)
        self.assertIn(".agent-toolkit", (self.project / "CLAUDE.md").read_text())

    def test_local_edit_is_reported_as_drift(self):
        self.install(["claude-code"])
        rules = sorted((self.project / ".agent-toolkit/skills").iterdir())
        target = rules[0] / "SKILL.md"
        target.write_text(target.read_text() + "\nlocal edit\n")
        modified, missing = inst.drift(self.project)
        self.assertTrue(modified, "edited file was not reported as drift")

    def test_reinstall_after_edit_keeps_the_edit_and_still_reports_drift(self):
        self.install(["claude-code"])
        skill = next(iter(sorted((self.project / ".agent-toolkit/skills").iterdir())))
        target = skill / "SKILL.md"
        target.write_text("EDITED\n")
        self.install(["claude-code"])
        self.assertEqual(target.read_text(), "EDITED\n")
        modified, _ = inst.drift(self.project)
        self.assertTrue(modified, "drift disappeared after reinstall")


# ----------------------------------------------------------------------
class TestMcp(TempProject):
    def test_foreign_servers_survive_install_and_uninstall(self):
        self.write(".mcp.json", json.dumps(
            {"mcpServers": {"mine": {"command": "node", "args": ["s.js"]}}}))
        self.install(["claude-code"], packs=["superpowers", "mcp-context7"])

        doc = json.loads((self.project / ".mcp.json").read_text())
        self.assertIn("mine", doc["mcpServers"])
        self.assertIn("context7", doc["mcpServers"])

        inst.uninstall(self.project, self.registry, report=Report())
        doc = json.loads((self.project / ".mcp.json").read_text())
        self.assertIn("mine", doc["mcpServers"])
        self.assertNotIn("context7", doc["mcpServers"])

    def test_vscode_uses_its_own_key_and_shape(self):
        spec = ServerSpec.from_json(
            ROOT / "catalog/packs/mcp-context7/files/mcp/context7.json")
        entry = shape_entry(spec, "vscode")
        self.assertEqual(entry["type"], "stdio")

    def test_opencode_shape_uses_command_array(self):
        spec = ServerSpec.from_json(
            ROOT / "catalog/packs/mcp-context7/files/mcp/context7.json")
        entry = shape_entry(spec, "opencode")
        self.assertIsInstance(entry["command"], list)
        self.assertEqual(entry["type"], "local")

    def test_url_server_shapes_as_http(self):
        spec = ServerSpec.from_json(
            ROOT / "catalog/packs/mcp-figma/files/mcp/figma.json")
        self.assertTrue(spec.url)
        entry = shape_entry(spec, "standard")
        self.assertEqual(entry["url"], spec.url)
        self.assertNotIn("command", entry)

    def test_specs_declare_their_manual_requirements(self):
        figma = ServerSpec.from_json(
            ROOT / "catalog/packs/mcp-figma/files/mcp/figma.json")
        self.assertTrue(figma.needs_manual_setup)


# ----------------------------------------------------------------------
class TestUninstall(TempProject):
    def test_restores_the_project(self):
        self.write("package.json", '{"name":"x"}')
        self.install(["claude-code", "cursor", "windsurf"])
        inst.uninstall(self.project, self.registry, report=Report())
        left = sorted(p.name for p in self.project.iterdir())
        self.assertEqual(left, ["package.json"])

    def test_keeps_files_it_did_not_generate(self):
        self.install(["claude-code"])
        (self.project / "CLAUDE.md").write_text("# hand written\n")
        inst.uninstall(self.project, self.registry, report=Report())
        self.assertTrue((self.project / "CLAUDE.md").exists())

    def test_uninstall_without_install_is_an_error(self):
        with self.assertRaises(ToolkitError):
            inst.uninstall(self.project, self.registry, report=Report())


# ----------------------------------------------------------------------
class TestRenderedContext(TempProject):
    """CORE.md must stay a router; bulk content belongs in files it points to."""

    def test_core_md_is_small(self):
        self.install(["claude-code"], packs=["superpowers", "security"])
        core = (self.project / ".agent-toolkit/CORE.md").read_text()
        self.assertLess(len(core), 6000,
                        "CORE.md is growing into a rulebook; keep it a router")

    def test_core_md_does_not_inline_rule_bodies(self):
        self.install(["claude-code"], packs=["security"])
        core = (self.project / ".agent-toolkit/CORE.md").read_text()
        rule = (self.project / ".agent-toolkit/rules/SECURITY.md").read_text()
        # a distinctive middle chunk of the rule must NOT appear in CORE.md
        chunk = rule[len(rule) // 2: len(rule) // 2 + 120].strip()
        if chunk:
            self.assertNotIn(chunk, core)

    def test_instruction_files_point_at_the_toolkit(self):
        self.install(["claude-code"])
        self.assertIn(".agent-toolkit", (self.project / "CLAUDE.md").read_text())

    def test_user_additions_below_the_marker_survive(self):
        self.install(["claude-code"])
        core_path = self.project / ".agent-toolkit/CORE.md"
        core_path.write_text(core_path.read_text() + "\n## My project note\nkeep me\n")
        self.install(["claude-code"])
        self.assertIn("keep me", core_path.read_text())


# ----------------------------------------------------------------------
class TestWorkflowTrigger(TempProject):
    """The workflow is useless if there is no way to start it."""

    def test_claude_gets_slash_commands(self):
        self.install(["claude-code"])
        cmds = self.project / ".claude/commands"
        for name in ("plan.md", "plan-status.md", "plan-resume.md"):
            self.assertTrue((cmds / name).is_file(), name)

    def test_plan_command_has_frontmatter(self):
        self.install(["claude-code"])
        text = (self.project / ".claude/commands/plan.md").read_text()
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("description:", text)
        self.assertIn("$ARGUMENTS", text)

    def test_plan_command_enforces_the_gate(self):
        self.install(["claude-code"])
        text = (self.project / ".claude/commands/plan.md").read_text()
        self.assertIn("11-gate.md", text)
        self.assertIn("wait for", text.lower())

    def test_agents_without_commands_get_no_command_dir(self):
        self.install(["cursor"])
        self.assertFalse((self.project / ".claude").exists())
        self.assertTrue((self.project / ".agent-toolkit/START-HERE.md").is_file())

    def test_start_here_exists_for_every_agent(self):
        for agent in ("claude-code", "cursor", "codex", "aider"):
            with self.subTest(agent=agent):
                self.setUp()
                self.install([agent])
                self.assertTrue(
                    (self.project / ".agent-toolkit/START-HERE.md").is_file()
                )

    def test_no_machine_specific_paths_are_baked_in(self):
        """These files get committed; a path from one machine breaks everyone."""
        self.install(["claude-code"])
        home = str(Path.home())
        for rel in (".agent-toolkit/CORE.md", ".agent-toolkit/START-HERE.md",
                    ".claude/commands/plan.md"):
            text = (self.project / rel).read_text()
            self.assertNotIn(home, text, f"{rel} leaks an absolute home path")
            self.assertNotIn(str(ROOT), text, f"{rel} leaks the toolkit checkout path")

    def test_embedded_install_uses_the_embedded_launcher(self):
        self.install(["claude-code"])
        embedlib.embed(ROOT, self.project, with_vendor=False, force=False,
                       report=Report())
        # re-render now that the launcher exists
        self.install(["claude-code"], force=True)
        text = (self.project / ".claude/commands/plan.md").read_text()
        self.assertIn("./.agent-toolkit/toolkit/uat", text)


class TestSkillPrecedence(TempProject):
    """The workflow must resolve every conflict with the vendored skills."""

    def readme(self):
        return (ROOT / "catalog/workflow/README.md").read_text()

    def test_precedence_rule_is_stated(self):
        text = self.readme()
        self.assertIn("Phases own the sequence and the gates", text)
        self.assertIn("Skills own the technique", text)

    def test_all_four_known_conflicts_are_addressed(self):
        text = self.readme().lower()
        for topic in ("classify once", "batch questions", "one gate",
                      "terminal states"):
            self.assertIn(topic, text, f"precedence does not cover: {topic}")

    def test_triage_maps_to_the_skill_vocabulary(self):
        text = (ROOT / "catalog/workflow/00-triage.md").read_text()
        for word in ("Bounded", "Architectural", "Spike"):
            self.assertIn(word, text, f"triage does not map {word}")

    def test_plan_phase_delegates_rather_than_redefining(self):
        text = (ROOT / "catalog/workflow/10-plan.md").read_text()
        self.assertIn("writing-plans", text)
        self.assertIn("docs/superpowers/plans/", text)
        self.assertIn("does not define a plan format", text)

    def test_execute_phase_delegates_to_superpowers(self):
        text = (ROOT / "catalog/workflow/12-execute.md").read_text()
        for skill in ("subagent-driven-development", "executing-plans",
                      "finishing-a-development-branch", "using-git-worktrees"):
            self.assertIn(skill, text, skill)

    def test_design_runs_after_stack_and_architecture(self):
        wf = ROOT / "catalog/workflow"
        self.assertTrue((wf / "04-stack.md").is_file())
        self.assertTrue((wf / "06-architecture.md").is_file())
        self.assertTrue((wf / "08-design.md").is_file())
        design = (wf / "08-design.md").read_text()
        self.assertIn("docs/architecture.md", design)
        self.assertIn("docs/stack.md", design)

    def test_every_phase_file_is_numbered_contiguously(self):
        wf = ROOT / "catalog/workflow"
        nums = sorted(f.name[:2] for f in wf.glob("[0-9][0-9]-*.md"))
        self.assertEqual(nums, [f"{i:02d}" for i in range(13)])

    def test_skills_named_by_phases_are_actually_vendored(self):
        """A phase must not reference a skill the toolkit cannot install."""
        import re
        available = {d.name for d in (ROOT / "vendor/superpowers/skills").iterdir()
                     if d.is_dir()}
        for phase in sorted((ROOT / "catalog/workflow").glob("[0-9][0-9]-*.md")):
            for ref in re.findall(r"\.\./skills/([a-z0-9-]+)/SKILL\.md", phase.read_text()):
                self.assertIn(ref, available,
                              f"{phase.name} references unvendored skill {ref}")


class TestVendorReachability(unittest.TestCase):
    def test_no_vendored_skill_is_unreachable(self):
        from uat.catalog import unreachable_vendor_content
        orphans = unreachable_vendor_content(Catalog.load(ROOT), ROOT)
        self.assertEqual(orphans, {}, f"vendored but no pack installs it: {orphans}")


class TestLongTailRules(TempProject):
    """Everything vendored must be installable, pack or no pack."""

    def test_every_vendored_rule_document_is_resolvable(self):
        from uat.catalog import find_rule_document, iter_rule_documents
        docs = list(iter_rule_documents(ROOT))
        self.assertGreater(len(docs), 400)
        for vendor, rel, stem, _ in docs:
            with self.subTest(doc=f"{vendor}:{stem}"):
                v, r, s_, _p = find_rule_document(ROOT, f"{vendor}:{stem}")
                self.assertEqual((v, r), (vendor, rel))

    def test_search_finds_by_substring(self):
        from uat.catalog import search_rule_documents
        self.assertTrue(search_rule_documents(ROOT, "wordpress"))
        self.assertEqual(search_rule_documents(ROOT, "zzz-not-a-real-thing"), [])

    def test_unknown_rule_is_a_clear_error(self):
        from uat.catalog import find_rule_document
        with self.assertRaises(ToolkitError):
            find_rule_document(ROOT, "awesome-copilot:definitely-not-here")

    def test_add_rule_installs_and_refreshes_the_router(self):
        from uat.catalog import find_rule_document
        from uat.util import copy_file
        self.install(["claude-code"])
        vendor, rel, stem, src = find_rule_document(ROOT, "awesome-copilot:memory-bank")
        dest = self.project / ".agent-toolkit/rules/MEMORY_BANK.md"
        report = Report()
        copy_file(src, dest, force=False, report=report)
        inst.refresh(self.project, ROOT, self.registry, report=report)
        self.assertTrue(dest.is_file())
        self.assertIn("MEMORY_BANK.md",
                      (self.project / ".agent-toolkit/CORE.md").read_text())

    def test_refresh_preserves_user_additions(self):
        self.install(["claude-code"])
        core = self.project / ".agent-toolkit/CORE.md"
        core.write_text(core.read_text() + "\n## Project note\nkeep me\n")
        inst.refresh(self.project, ROOT, self.registry, report=Report())
        self.assertIn("keep me", core.read_text())

    def test_refresh_without_install_is_an_error(self):
        with self.assertRaises(ToolkitError):
            inst.refresh(self.project, ROOT, self.registry, report=Report())


class TestSessionHook(TempProject):
    """The hook is what turns 'available' into 'actually used'."""

    def install_hook(self, force=False):
        return self.install(["claude-code"],
                            packs=["superpowers", "session-reminder"], force=force)

    def test_hook_script_is_installed_and_executable(self):
        self.install_hook()
        script = self.project / ".agent-toolkit/hooks/session-start.sh"
        self.assertTrue(script.is_file())
        self.assertTrue(os.access(script, os.X_OK))

    def test_hook_is_registered_in_settings(self):
        self.install_hook()
        doc = json.loads((self.project / ".claude/settings.json").read_text())
        entries = doc["hooks"]["SessionStart"]
        self.assertTrue(any(".agent-toolkit" in json.dumps(e) for e in entries))

    def test_existing_user_settings_survive(self):
        self.write(".claude/settings.json", json.dumps(
            {"permissions": {"allow": ["Bash(npm test)"]},
             "hooks": {"SessionStart": [
                 {"matcher": "startup",
                  "hooks": [{"type": "command", "command": "echo mine"}]}]}}))
        self.install_hook()
        doc = json.loads((self.project / ".claude/settings.json").read_text())
        self.assertEqual(doc["permissions"]["allow"], ["Bash(npm test)"])
        self.assertEqual(len(doc["hooks"]["SessionStart"]), 2)

    def test_uninstall_removes_ours_and_keeps_theirs(self):
        self.write(".claude/settings.json", json.dumps(
            {"hooks": {"SessionStart": [
                {"matcher": "startup",
                 "hooks": [{"type": "command", "command": "echo mine"}]}]}}))
        self.install_hook()
        inst.uninstall(self.project, self.registry, report=Report())
        doc = json.loads((self.project / ".claude/settings.json").read_text())
        entries = doc["hooks"]["SessionStart"]
        self.assertEqual(len(entries), 1)
        self.assertIn("echo mine", json.dumps(entries))

    def test_reinstall_does_not_duplicate_the_hook(self):
        self.install_hook()
        self.install_hook()
        doc = json.loads((self.project / ".claude/settings.json").read_text())
        ours = [e for e in doc["hooks"]["SessionStart"]
                if ".agent-toolkit" in json.dumps(e)]
        self.assertEqual(len(ours), 1)

    def test_hook_output_names_the_gate_and_safety(self):
        import subprocess
        self.install_hook()
        script = self.project / ".agent-toolkit/hooks/session-start.sh"
        out = subprocess.run(["bash", str(script)], capture_output=True, text=True,
                             env={**os.environ,
                                  "CLAUDE_PROJECT_DIR": str(self.project)})
        self.assertEqual(out.returncode, 0)
        for expected in ("11-gate.md", "SAFETY.md", "00-triage.md", "workflow"):
            self.assertIn(expected, out.stdout, expected)

    def test_hook_is_silent_outside_a_configured_project(self):
        import subprocess
        self.install_hook()
        script = self.project / ".agent-toolkit/hooks/session-start.sh"
        out = subprocess.run(["bash", str(script)], capture_output=True, text=True,
                             env={**os.environ, "CLAUDE_PROJECT_DIR": str(self.tmp)})
        self.assertEqual(out.returncode, 0)
        self.assertEqual(out.stdout.strip(), "")

    def test_agents_without_hook_support_get_none(self):
        self.install(["cursor"], packs=["superpowers", "session-reminder"])
        self.assertFalse((self.project / ".claude").exists())


class TestEmbedding(TempProject):
    """Embedding must keep the project self-contained without adding folders."""

    def embed(self, with_vendor=False):
        self.install(["claude-code"])
        return embedlib.embed(
            ROOT, self.project, with_vendor=with_vendor, force=False, report=Report()
        )

    def test_embeds_inside_the_single_folder(self):
        self.embed()
        self.assertTrue((self.project / ".agent-toolkit/toolkit/uat").is_file())
        # no new top-level directory appeared
        top = {p.name for p in self.project.iterdir()}
        self.assertTrue(top.issubset({".agent-toolkit", ".claude", ".mcp.json", "CLAUDE.md"}))

    def test_embedded_launcher_is_executable(self):
        dest = self.embed()
        self.assertTrue(os.access(dest / "uat", os.X_OK))

    def test_factory_only_directories_are_not_embedded(self):
        dest = self.embed()
        for skipped in ("tests", "docs", "bin", ".git"):
            self.assertFalse((dest / skipped).exists(), f"{skipped} should not embed")

    def test_slim_embed_omits_vendor(self):
        dest = self.embed(with_vendor=False)
        self.assertFalse((dest / "vendor").exists())
        self.assertTrue((dest / "catalog").is_dir())
        info = embedlib.embed_info(dest)
        self.assertFalse(info["with_vendor"])

    def test_full_embed_includes_vendor(self):
        dest = self.embed(with_vendor=True)
        self.assertTrue((dest / "vendor/superpowers/skills/brainstorming/SKILL.md").is_file())
        self.assertTrue(embedlib.embed_info(dest)["with_vendor"])

    def test_embedded_copy_resolves_its_own_root(self):
        """cli.TOOLKIT_ROOT must point at the embedded copy, not the factory."""
        dest = self.embed()
        cli_path = dest / "src/uat/cli.py"
        self.assertTrue(cli_path.is_file())
        self.assertEqual(cli_path.resolve().parents[2], dest.resolve())

    def test_embedded_copy_can_install_from_itself(self):
        dest = self.embed(with_vendor=True)
        registry = Registry.load(dest)
        catalog = Catalog.load(dest)
        plan = inst.build_plan(
            dest, self.project, registry=registry, catalog=catalog,
            agent_keys=["claude-code"], mode="focused", explicit_packs=["go"],
        )
        inst.execute(plan, dest)
        rule = self.project / ".agent-toolkit/rules/GO.md"
        self.assertTrue(rule.is_file())
        self.assertGreater(len(rule.read_text()), 5000)

    def test_is_embedded_marker(self):
        dest = self.embed()
        self.assertTrue(embedlib.is_embedded(dest))
        self.assertFalse(embedlib.is_embedded(ROOT))


class TestWorkflowShipped(TempProject):
    def test_workflow_phases_are_installed(self):
        self.install(["claude-code"])
        wf = self.project / ".agent-toolkit/workflow"
        self.assertTrue((wf / "README.md").exists())
        for phase in ("00-triage", "01-discovery", "10-plan", "11-gate", "12-execute"):
            self.assertTrue((wf / f"{phase}.md").exists(), phase)

    def test_core_policy_is_installed(self):
        self.install(["claude-code"])
        core = self.project / ".agent-toolkit/core"
        for f in ("SAFETY.md", "GIT.md", "VERIFICATION.md", "INTERACTION_MODES.md"):
            self.assertTrue((core / f).exists(), f)


if __name__ == "__main__":
    unittest.main(verbosity=2)
