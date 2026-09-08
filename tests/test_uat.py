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

    def test_agents_with_native_skill_support(self):
        """Codex reads repository skills from .agents/skills - verified in docs."""
        with_skills = sorted(a.id for a in self.registry if a.supports_skills)
        self.assertEqual(with_skills, ["claude-code", "codex"])
        self.assertEqual(self.registry.get("codex").skills_path, ".agents/skills")

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

    def test_user_scoped_server_is_documented_not_written(self):
        """Claude Design belongs to an account, not to a committed repo.

        Writing it into .mcp.json would give every teammate an entry that
        cannot work until they personally sign in - and the toolkit never
        writes outside the project, so documenting is the only honest option.
        """
        spec = ServerSpec.from_json(
            ROOT / "catalog/packs/mcp-claude-design/files/mcp/claude-design.json")
        self.assertEqual(spec.scope, "user")

        self.install(["claude-code"], packs=["mcp-claude-design"])
        self.assertFalse(
            (self.project / ".mcp.json").exists(),
            "a user-scoped server must not be written into the project config")

        notes = (self.project / ".agent-toolkit/mcp/README.md").read_text()
        self.assertIn("claude-design", notes)
        self.assertIn("--scope user", notes)

    def test_project_scoped_servers_are_still_written(self):
        self.install(["claude-code"], packs=["mcp-context7"])
        doc = json.loads((self.project / ".mcp.json").read_text())
        self.assertIn("context7", doc["mcpServers"])

    def test_unknown_scope_is_rejected(self):
        bad = self.project / "bad.json"
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text(json.dumps(
            {"name": "x", "url": "https://example.test/mcp", "scope": "global"}))
        with self.assertRaises(ToolkitError):
            ServerSpec.from_json(bad)


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
        for topic in ("classify once", "batch questions", "one stop",
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
        self.assertEqual(nums, [f"{i:02d}" for i in range(14)])

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


class TestVerifiedAgentSpecs(unittest.TestCase):
    """Specs checked against each tool's own docs. Values, not vibes.

    Each assertion below corresponds to something read from official
    documentation; see the `notes` field of the agent in catalog/agents.json.
    """

    def setUp(self):
        self.registry = Registry.load(ROOT)

    def test_vscode_uses_servers_not_mcpservers(self):
        a = self.registry.get("copilot")
        self.assertEqual(a.mcp["path"], ".vscode/mcp.json")
        self.assertEqual(a.mcp["key"], "servers")

    def test_gemini_project_settings_and_key(self):
        a = self.registry.get("gemini-cli")
        self.assertEqual(a.mcp["path"], ".gemini/settings.json")
        self.assertEqual(a.mcp["key"], "mcpServers")
        self.assertEqual(a.instruction_path, "GEMINI.md")

    def test_cline_uses_the_directory_form(self):
        a = self.registry.get("cline")
        self.assertTrue(a.instruction_path.startswith(".clinerules/"))

    def test_roo_uses_the_directory_form(self):
        a = self.registry.get("roo")
        self.assertTrue(a.instruction_path.startswith(".roo/rules/"))

    def test_opencode_mcp_shape_matches_the_docs(self):
        spec = ServerSpec.from_json(
            ROOT / "catalog/packs/mcp-context7/files/mcp/context7.json")
        entry = shape_entry(spec, "opencode")
        self.assertEqual(entry["type"], "local")
        self.assertIsInstance(entry["command"], list)
        self.assertTrue(entry["enabled"])

    def test_opencode_remote_shape_matches_the_docs(self):
        spec = ServerSpec.from_json(
            ROOT / "catalog/packs/mcp-figma/files/mcp/figma.json")
        entry = shape_entry(spec, "opencode")
        self.assertEqual(entry["type"], "remote")
        self.assertIn("url", entry)

    def test_zed_writes_dot_rules(self):
        """.rules is first in Zed's precedence list, ahead of AGENTS.md."""
        self.assertEqual(self.registry.get("zed").instruction_path, ".rules")

    def test_junie_uses_agents_md_not_the_legacy_path(self):
        a = self.registry.get("junie")
        self.assertEqual(a.instruction_path, "AGENTS.md")
        self.assertNotIn(".junie/guidelines.md", a.owned_paths())

    def test_amp_uses_agents_md(self):
        self.assertEqual(self.registry.get("amp").instruction_path, "AGENTS.md")

    def test_aider_gets_a_loader_config(self):
        """CONVENTIONS.md is inert without a read: entry."""
        a = self.registry.get("aider")
        self.assertEqual(a.surfaces["config"]["path"], ".aider.conf.yml")
        self.assertIn(".aider.conf.yml", a.owned_paths())

    def test_legacy_paths_are_justified_in_notes(self):
        """A medium-confidence agent must explain why, not just be unverified."""
        for a in self.registry:
            if a.confidence == "medium":
                self.assertTrue(
                    len(a.notes) > 80,
                    f"{a.id} is medium confidence with no explanation",
                )

    def test_no_agent_is_low_confidence_anymore(self):
        low = [a.id for a in self.registry if a.confidence == "low"]
        self.assertEqual(low, [], f"unverified agent specs remain: {low}")


class TestAiderLoaderConfig(TempProject):
    def test_conventions_file_is_actually_wired_up(self):
        self.install(["aider"])
        conf = self.project / ".aider.conf.yml"
        self.assertTrue(conf.is_file())
        self.assertIn("read: CONVENTIONS.md", conf.read_text())

    def test_existing_config_is_not_clobbered(self):
        self.write(".aider.conf.yml", "model: gpt-4\n")
        result = self.install(["aider"])
        self.assertEqual((self.project / ".aider.conf.yml").read_text(),
                         "model: gpt-4\n")
        self.assertTrue(any("aider" in n.lower() for n in result.notes),
                        "user was not told to add the read: line themselves")

    def test_uninstall_removes_it(self):
        self.install(["aider"])
        inst.uninstall(self.project, self.registry, report=Report())
        self.assertFalse((self.project / ".aider.conf.yml").exists())


class TestReportedRegressions(TempProject):
    """One test per bug from the reproduction report. Each one failed before."""

    # --- 2: uninstall deleted instructions it never wrote -----------------
    def test_uninstall_keeps_a_users_own_instruction_file(self):
        self.write("CLAUDE.md",
                   "# Team rules\nSee .agent-toolkit/CORE.md for the toolkit.\n")
        self.install(["claude-code"])
        inst.uninstall(self.project, self.registry, report=Report())
        self.assertTrue((self.project / "CLAUDE.md").is_file())
        self.assertIn("Team rules", (self.project / "CLAUDE.md").read_text())

    def test_uninstall_keeps_a_generated_file_the_user_edited(self):
        self.install(["claude-code"])
        target = self.project / "CLAUDE.md"
        target.write_text(target.read_text() + "\n## my addition\n")
        inst.uninstall(self.project, self.registry, report=Report())
        self.assertTrue(target.is_file())
        self.assertIn("my addition", target.read_text())

    def test_uninstall_still_removes_untouched_generated_files(self):
        self.install(["claude-code"])
        inst.uninstall(self.project, self.registry, report=Report())
        self.assertFalse((self.project / "CLAUDE.md").exists())

    # --- 3: a second install forgot the first -----------------------------
    def test_add_pack_keeps_previous_packs_agents_and_mode(self):
        first = self.install(["claude-code", "cursor"],
                             packs=["superpowers", "security"], mode="autonomous")
        before = set(first.plan.pack_ids)

        state = inst.load_state(self.project)
        doc = inst.read_json(self.project / ".agent-toolkit/project.json", default={})
        merged = sorted(set(state["packs"]) | {"go"})
        agents = list(dict.fromkeys(["claude-code"] + state["agents"]))
        plan = inst.build_plan(
            ROOT, self.project, registry=self.registry, catalog=self.catalog,
            agent_keys=agents, mode=doc["mode"], explicit_packs=merged)
        inst.execute(plan, ROOT)

        after = inst.load_state(self.project)
        self.assertTrue(before.issubset(set(after["packs"])), "packs were dropped")
        self.assertIn("go", after["packs"])
        self.assertEqual(after["agents"], ["claude-code", "cursor"])
        self.assertEqual(
            inst.read_json(self.project / ".agent-toolkit/project.json")["mode"],
            "autonomous")

    # --- 4: empty reports counted as completed phases ---------------------
    def test_empty_report_is_a_stub_not_a_completed_phase(self):
        from uat.cli import report_substance
        self.install(["claude-code"])
        r = self.project / ".agent-toolkit/reports/01-discovery.md"
        r.write_text("")
        self.assertEqual(report_substance(r)[0], "stub")
        r.write_text("# Phase 01\n\n## What was checked\n\n## Decisions\n")
        self.assertEqual(report_substance(r)[0], "stub",
                         "an unfilled template is not a completed phase")
        r.write_text("# Phase 01 - discovery\n\nEmpty repository: no manifests, "
                     "no CI, no tests. Treating this as a new project and asking "
                     "about hosting before proposing a stack.\n")
        self.assertEqual(report_substance(r)[0], "done")

    def test_triage_expects_no_report(self):
        from uat.cli import PHASES
        by = {num: expects for num, _n, _a, expects in PHASES}
        self.assertFalse(by["00"], "triage writes no file; expecting one loops forever")
        self.assertTrue(by["01"])

    def test_session_hook_does_not_ask_for_a_triage_report(self):
        import subprocess
        self.install(["claude-code"], packs=["superpowers", "session-reminder"])
        out = subprocess.run(
            ["bash", str(self.project / ".agent-toolkit/hooks/session-start.sh")],
            capture_output=True, text=True,
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(self.project)})
        self.assertIn("next phase: 01", out.stdout)

    # --- 6: dry runs were unreliable --------------------------------------
    def test_dry_run_creates_nothing(self):
        target = self.tmp / "untouched"
        target.mkdir()
        plan = inst.build_plan(
            ROOT, target, registry=self.registry, catalog=self.catalog,
            agent_keys=["claude-code"], mode="focused",
            explicit_packs=["superpowers"])
        inst.execute(plan, ROOT, dry_run=True)
        self.assertEqual(list(target.iterdir()), [],
                         "dry run wrote something into the project")

    def test_dry_run_reports_commands_and_skill_mount(self):
        plan = inst.build_plan(
            ROOT, self.project, registry=self.registry, catalog=self.catalog,
            agent_keys=["claude-code"], mode="focused",
            explicit_packs=["superpowers"])
        result = inst.execute(plan, ROOT, dry_run=True)
        paths = " ".join(a.path for a in result.report.actions)
        self.assertIn("commands/plan.md", paths, "dry run omitted slash commands")
        self.assertIn(".claude/skills", paths, "dry run omitted the skill mount")

    # --- 5: Codex skills --------------------------------------------------
    def test_codex_gets_a_skill_mount(self):
        self.install(["codex"])
        mount = self.project / ".agents/skills"
        self.assertTrue(mount.is_symlink() or mount.is_dir())
        self.assertTrue((mount / "brainstorming/SKILL.md").exists())


class TestRollbackRestartsTheService(unittest.TestCase):
    """Rollback moved the symlink but never restarted a systemd-managed app,
    so the old release was restored on disk and the broken one kept serving.
    And a failed restart exited before rollback could run at all."""

    DEPLOY = ROOT / "catalog/packs/deploy-ubuntu/files/deploy"

    def setUp(self):
        import shutil
        self.tmp = Path(tempfile.mkdtemp(prefix="uat-sysd-"))
        self.app = self.tmp / "app"
        (self.app / "releases" / "GOOD-OLD").mkdir(parents=True)
        (self.app / "shared").mkdir()
        (self.app / "shared" / ".env").write_text("")
        (self.app / "current").symlink_to(self.app / "releases" / "GOOD-OLD")
        src = self.tmp / "src"; src.mkdir(); (src / "marker").write_text("new")
        self.deploy = self.tmp / "deploy"
        shutil.copytree(self.DEPLOY, self.deploy)
        (self.deploy / "deploy.env").write_text(
            f"APP_NAME=probe\nAPP_USER=nobody\nAPP_DIR={self.app}\n"
            f"APP_DOMAIN=localhost\nAPP_PORT=59995\nAPP_REPO=\n"
            f"APP_SOURCE={src}\nBUILD_CMD=\nMIGRATE_CMD=\nRESTART_CMD=\n"
            f"HEALTH_PATH=/\nHEALTH_ATTEMPTS=1\n")
        self.bin = self.tmp / "bin"; self.bin.mkdir()
        self.log = self.tmp / "restarts.log"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _stub_systemctl(self, restart_exit: int):
        stub = self.bin / "systemctl"
        stub.write_text(
            "#!/bin/sh\n"
            'case "$1" in\n'
            '  list-unit-files) echo "probe.service enabled";;\n'
            f'  restart) echo "$2" >> "{self.log}"; exit {restart_exit};;\n'
            "esac\nexit 0\n")
        stub.chmod(0o755)

    def _deploy(self):
        import subprocess
        return subprocess.run(
            ["bash", str(self.deploy / "deploy.sh"), "--env",
             str(self.deploy / "deploy.env")],
            capture_output=True, text=True, cwd=self.deploy, timeout=120,
            env={**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}"})

    def test_rollback_restarts_the_service(self):
        self._stub_systemctl(0)
        self._deploy()
        self.assertEqual(os.path.basename(os.path.realpath(self.app / "current")),
                         "GOOD-OLD")
        restarts = self.log.read_text().split() if self.log.exists() else []
        self.assertEqual(len(restarts), 2,
                         "expected a restart for the deploy and one for the "
                         f"rollback, got {restarts}")

    def test_a_failed_restart_triggers_rollback(self):
        self._stub_systemctl(1)
        out = self._deploy()
        self.assertIn("rolling back", out.stdout + out.stderr)
        self.assertEqual(os.path.basename(os.path.realpath(self.app / "current")),
                         "GOOD-OLD")

    def test_dry_run_on_a_server_with_no_releases_directory(self):
        """Pruning assumed releases/ existed and exited during the preview."""
        import shutil, subprocess
        shutil.rmtree(self.app / "releases")
        (self.app / "current").unlink()
        self._stub_systemctl(0)
        out = subprocess.run(
            ["bash", str(self.deploy / "deploy.sh"), "--env",
             str(self.deploy / "deploy.env"), "--dry-run"],
            capture_output=True, text=True, cwd=self.deploy, timeout=120,
            env={**os.environ, "DRY_RUN": "1",
                 "PATH": f"{self.bin}:{os.environ['PATH']}"})
        self.assertEqual(out.returncode, 0,
                         f"dry run failed:\n{out.stdout}\n{out.stderr}")
        self.assertIn("nothing to prune", out.stdout)


class TestSecondRoundRegressions(TempProject):
    """Second reproduction round. Each failed against the previous fix."""

    # --- 1: empty ownership map was mistaken for a legacy install ----------
    def test_empty_agent_files_is_not_treated_as_legacy(self):
        """Every candidate file pre-existed, so we own none - not 'unknown'."""
        (self.project / ".agents" / "skills").mkdir(parents=True)
        self.write("AGENTS.md", "# Team AGENTS\nSee .agent-toolkit/CORE.md\n")
        self.install(["codex"])
        state = inst.load_state(self.project)
        self.assertIn("agent_files", state)
        self.assertEqual(state["agent_files"], {}, "test premise changed")
        inst.uninstall(self.project, self.registry, report=Report())
        self.assertTrue((self.project / "AGENTS.md").is_file(),
                        "uninstall deleted a file it never wrote")
        self.assertIn("Team AGENTS", (self.project / "AGENTS.md").read_text())

    def test_pre_provenance_install_still_cleans_up(self):
        """A real legacy install has no agent_files key at all."""
        self.install(["claude-code"])
        sf = self.project / ".agent-toolkit/installed.json"
        state = json.loads(sf.read_text())
        del state["agent_files"]
        sf.write_text(json.dumps(state))
        inst.uninstall(self.project, self.registry, report=Report())
        self.assertFalse((self.project / "CLAUDE.md").exists())

    # --- 3b: dry run omitted the MCP config ------------------------------
    def test_dry_run_previews_mcp_config(self):
        plan = inst.build_plan(
            ROOT, self.project, registry=self.registry, catalog=self.catalog,
            agent_keys=["claude-code"], mode="focused",
            explicit_packs=["superpowers", "mcp-context7"])
        result = inst.execute(plan, ROOT, dry_run=True)
        paths = " ".join(a.path for a in result.report.actions)
        self.assertIn(".mcp.json", paths, "dry run omitted the MCP config")
        self.assertTrue(result.mcp_specs, "dry run predicted no servers")

    # --- 4a: hook and CLI disagreed on what counts as a report ------------
    def test_hook_and_cli_agree_on_heading_only_reports(self):
        import subprocess
        self.install(["claude-code"], packs=["superpowers", "session-reminder"])
        reports = self.project / ".agent-toolkit/reports"
        for n in range(1, 14):
            (reports / f"{n:02d}-x.md").write_text("# TODO\n" * 10)

        from uat.cli import report_substance
        verdicts = {report_substance(reports / f"{n:02d}-x.md")[0]
                    for n in range(1, 14)}
        self.assertEqual(verdicts, {"stub"}, "CLI accepted heading-only reports")

        out = subprocess.run(
            ["bash", str(self.project / ".agent-toolkit/hooks/session-start.sh")],
            capture_output=True, text=True,
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(self.project)})
        self.assertIn("0 phase report(s)", out.stdout,
                      "hook counted heading-only files as completed phases")

    def test_hook_accepts_a_real_report(self):
        import subprocess
        self.install(["claude-code"], packs=["superpowers", "session-reminder"])
        (self.project / ".agent-toolkit/reports/01-discovery.md").write_text(
            "# Phase 01 - discovery\n\nEmpty repository: no manifests, no CI and "
            "no tests. Treating this as a new project, and asking about hosting "
            "before proposing a stack.\n")
        out = subprocess.run(
            ["bash", str(self.project / ".agent-toolkit/hooks/session-start.sh")],
            capture_output=True, text=True,
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(self.project)})
        self.assertIn("1 phase report(s)", out.stdout)
        self.assertIn("next phase: 02", out.stdout)

    # --- 4b: a report without its artifact was still labelled done --------
    def test_report_without_its_artifact_is_a_gap(self):
        self.install(["claude-code"])
        (self.project / ".agent-toolkit/reports/06-architecture.md").write_text(
            "# Phase 06 - architecture\n\nModules: billing, auth, reporting. "
            "Postgres with row-level security for tenant isolation, and a "
            "database-backed job queue.\n")
        import subprocess
        out = subprocess.run(
            [str(ROOT / "bin/uat"), "workflow", "--project", str(self.project)],
            capture_output=True, text=True, env={**os.environ, "NO_COLOR": "1"})
        self.assertIn("gap", out.stdout, "missing artifact still counted as done")
        self.assertIn("docs/architecture.md", out.stdout)


class TestProductAcceptance(unittest.TestCase):
    """Per-task verification existed; product acceptance did not.

    docs/screens.md defined the user journeys and nothing downstream ever
    exercised them, so a rendering dashboard could pass while password reset
    was broken. Phase 13 closes that; these tests keep it closed.
    """

    WF = ROOT / "catalog/workflow"

    def test_acceptance_phase_exists(self):
        self.assertTrue((self.WF / "13-acceptance.md").is_file())

    def test_acceptance_consumes_the_flows_defined_in_phase_03(self):
        """The chain screens.md -> acceptance was the missing link."""
        a = (self.WF / "13-acceptance.md").read_text()
        self.assertIn("docs/screens.md", a)
        self.assertIn("docs/business-logic.md", a)

    def test_acceptance_rejects_a_green_suite_as_proof(self):
        a = (self.WF / "13-acceptance.md").read_text()
        self.assertIn("not acceptance", a)
        self.assertIn("NOT VERIFIED", a)

    def test_acceptance_names_the_flows_that_rot(self):
        a = (self.WF / "13-acceptance.md").read_text().lower()
        for flow in ("password reset", "permission", "payment", "sign-out"):
            self.assertIn(flow, a, f"acceptance does not mention {flow}")

    def test_verification_no_longer_accepts_a_screenshot_for_a_ui_change(self):
        v = (ROOT / "catalog/core/VERIFICATION.md").read_text()
        ui_row = [ln for ln in v.splitlines() if ln.startswith("| A UI change")]
        self.assertEqual(len(ui_row), 1)
        self.assertNotIn("screenshot or browser check", ui_row[0])
        self.assertIn("Rendered is not the same as works", v)

    def test_verification_requires_observing_through_a_second_path(self):
        v = " ".join((ROOT / "catalog/core/VERIFICATION.md").read_text().split())
        self.assertIn("different path than the one that caused it", v)

    def test_execute_hands_off_to_acceptance(self):
        e = (self.WF / "12-execute.md").read_text()
        self.assertIn("13", e)
        self.assertIn("not mean the journeys work", e)

    def test_acceptance_is_in_the_phase_table_and_the_cli(self):
        from uat.cli import PHASES
        nums = [n for n, _, _, _ in PHASES]
        self.assertIn("13", nums)
        self.assertIn("13-acceptance.md", (self.WF / "README.md").read_text())

    def test_session_hook_counts_the_acceptance_phase(self):
        hook = (ROOT / "catalog/packs/session-reminder/files/hooks/"
                "session-start.sh").read_text()
        self.assertIn("11 12 13", hook, "hook stops counting before acceptance")


class TestApprovalGateConsistency(unittest.TestCase):
    """The gate is stated in four places; they must not contradict each other.

    They did: the triage table said Task work went straight to implementation,
    11-gate.md said the gate is never skipped at any class, and the session
    hook demanded it universally. Read one way that means pointless approval
    stops on one-line fixes; read the other way it means implementing with no
    approval at all.

    The resolved rule: the APPROVAL never scales away, the REVIEW does.
    """

    WF = ROOT / "catalog/workflow"

    @staticmethod
    def _flat(text: str) -> str:
        """Collapse line wrapping and markdown emphasis, so prose assertions
        survive reformatting."""
        return " ".join(text.replace("*", "").replace("`", "").split())

    def readme(self):
        return self._flat((self.WF / "README.md").read_text())

    def gate(self):
        return self._flat((self.WF / "11-gate.md").read_text())

    def triage(self):
        return self._flat((self.WF / "00-triage.md").read_text())

    def test_gate_says_the_approval_never_scales_away(self):
        self.assertIn("approval is never skipped", self.gate())

    def test_gate_says_the_review_does_scale(self):
        g = self.gate()
        self.assertIn("scales with the class", g)
        for cls in ("Task", "Feature", "Product"):
            self.assertIn(cls, g, f"gate does not say what {cls} class presents")

    def test_triage_table_includes_the_gate_for_every_class(self):
        """The Task row used to read '01, then implement' - no approval at all."""
        raw = (self.WF / "README.md").read_text().splitlines()
        rows = [ln for ln in raw if ln.startswith(("| **Task**", "| **Feature**",
                                                  "| **Product**"))]
        self.assertEqual(len(rows), 3, "triage table changed shape")
        for row in rows:
            phases = row.rsplit("|", 2)[-2]
            self.assertTrue(
                "11" in phases or "all" in phases,
                f"class row omits the gate: {row}",
            )

    def test_readme_no_longer_claims_task_has_no_gate(self):
        self.assertNotIn("There is no phase 11", self.readme())

    def test_task_approval_is_one_stop_not_two(self):
        r = self.readme()
        self.assertIn("One stop, not two", r)
        self.assertIn("is phase 11", r)

    def test_size_check_carries_the_design_so_the_answer_can_be_approval(self):
        t = self.triage()
        self.assertIn("put the design in the question", t)
        self.assertIn("is the phase 11 approval", t)

    def test_no_surface_licenses_implementing_without_approval(self):
        banned = "going straight to implementation with tests. Do you want"
        for name in ("README.md", "00-triage.md", "11-gate.md"):
            self.assertNotIn(banned, self._flat((self.WF / name).read_text()), name)

    def test_session_hook_matches_the_workflow(self):
        hook = (ROOT / "catalog/packs/session-reminder/files/hooks/"
                "session-start.sh").read_text()
        self.assertIn("11-gate.md", hook)
        self.assertIn("human approval", hook)


class TestDeployRollback(unittest.TestCase):
    """Regression 1: a failed health check must actually roll back.

    wait_http used to call die(), which exits the script - so deploy.sh never
    reached its rollback branch and left `current` pointing at the broken
    release, contradicting the advertised behaviour.
    """

    DEPLOY = ROOT / "catalog/packs/deploy-ubuntu/files/deploy"

    def setUp(self):
        import shutil
        self.tmp = Path(tempfile.mkdtemp(prefix="uat-deploy-"))
        self.app = self.tmp / "app"
        (self.app / "releases" / "GOOD-OLD").mkdir(parents=True)
        (self.app / "shared").mkdir()
        (self.app / "shared" / ".env").write_text("")
        (self.app / "releases" / "GOOD-OLD" / "marker").write_text("old")
        (self.app / "current").symlink_to(self.app / "releases" / "GOOD-OLD")
        self.src = self.tmp / "src"
        self.src.mkdir()
        (self.src / "marker").write_text("new")
        self.deploy = self.tmp / "deploy"
        shutil.copytree(self.DEPLOY, self.deploy)
        (self.deploy / "deploy.env").write_text(
            f"APP_NAME=probe\nAPP_USER=nobody\nAPP_DIR={self.app}\n"
            f"APP_DOMAIN=localhost\nAPP_PORT=59997\nAPP_REPO=\n"
            f"APP_SOURCE={self.src}\nBUILD_CMD=\nMIGRATE_CMD=\nRESTART_CMD=\n"
            f"HEALTH_PATH=/\nHEALTH_ATTEMPTS=1\n"
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, script, *args):
        import subprocess
        return subprocess.run(
            ["bash", str(self.deploy / script), "--env", str(self.deploy / "deploy.env"),
             *args],
            capture_output=True, text=True, cwd=self.deploy, timeout=120,
        )

    def test_failed_health_check_rolls_back(self):
        out = self._run("deploy.sh")
        self.assertNotEqual(out.returncode, 0, "a failed deploy must exit non-zero")
        live = os.path.basename(os.path.realpath(self.app / "current"))
        self.assertEqual(live, "GOOD-OLD",
                         f"current points at {live}; rollback did not happen")
        self.assertIn("rolling back", out.stdout + out.stderr)

    def test_failed_release_is_kept_for_inspection(self):
        self._run("deploy.sh")
        releases = sorted(p.name for p in (self.app / "releases").iterdir())
        self.assertGreater(len(releases), 1, "the failed release was discarded")

    def test_dry_run_survives_a_configured_build_command(self):
        """Regression 6: dry run cd'd into a release directory it never made."""
        env = (self.deploy / "deploy.env").read_text().replace(
            "BUILD_CMD=", 'BUILD_CMD="echo building"')
        (self.deploy / "deploy.env").write_text(env)
        import subprocess
        out = subprocess.run(
            ["bash", str(self.deploy / "deploy.sh"),
             "--env", str(self.deploy / "deploy.env"), "--dry-run"],
            capture_output=True, text=True, cwd=self.deploy, timeout=120,
            env={**os.environ, "DRY_RUN": "1"},
        )
        self.assertEqual(out.returncode, 0,
                         f"dry run failed:\n{out.stdout}\n{out.stderr}")
        live = os.path.basename(os.path.realpath(self.app / "current"))
        self.assertEqual(live, "GOOD-OLD", "dry run changed the live release")


class TestLocalVendoring(unittest.TestCase):
    """Not everything worth vendoring lives in a public git repo."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="uat-local-"))
        # a fake toolkit root, so tests never touch the real vendor/
        self.root = self.tmp / "toolkit"
        (self.root / "catalog").mkdir(parents=True)
        (self.root / "catalog" / "vendor.json").write_text(
            json.dumps({"upstreams": []}), encoding="utf-8")
        self.src = self.tmp / "house-rules"
        (self.src / "skills" / "house-style").mkdir(parents=True)
        (self.src / "skills" / "house-style" / "SKILL.md").write_text(
            "---\nname: house-style\ndescription: ours\n---\n# House style\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_local_directory_can_be_vendored(self):
        vid, _ = vendorlib.add_local(
            self.root, self.src, vendor_id="house", license="Proprietary")
        self.assertEqual(vid, "house")
        self.assertTrue(
            (self.root / "vendor/house/skills/house-style/SKILL.md").is_file())

    def test_it_is_registered_and_verifiable(self):
        vendorlib.add_local(self.root, self.src, vendor_id="house",
                            license="Proprietary")
        ups = vendorlib.load_upstreams(self.root)
        self.assertEqual([u.id for u in ups], ["house"])
        self.assertTrue(ups[0].is_local)
        ok, detail = vendorlib.verify_one(ups[0], self.root)
        self.assertTrue(ok, detail)

    def test_editing_the_snapshot_fails_verification(self):
        vendorlib.add_local(self.root, self.src, vendor_id="house",
                            license="Proprietary")
        target = self.root / "vendor/house/skills/house-style/SKILL.md"
        target.write_text(target.read_text() + "\ntampered\n")
        ok, detail = vendorlib.verify_one(
            vendorlib.load_upstreams(self.root)[0], self.root)
        self.assertFalse(ok)
        self.assertIn("modified", detail)

    def test_resync_picks_up_source_changes(self):
        vendorlib.add_local(self.root, self.src, vendor_id="house",
                            license="Proprietary")
        (self.src / "skills" / "house-style" / "SKILL.md").write_text(
            "---\nname: house-style\ndescription: ours\n---\n# Updated\n")
        status, _ = vendorlib.sync_one(
            vendorlib.load_upstreams(self.root)[0], self.root)
        self.assertEqual(status, "synced")
        self.assertIn("Updated",
                      (self.root / "vendor/house/skills/house-style/SKILL.md").read_text())

    def test_missing_source_still_verifies_the_snapshot(self):
        """A teammate cloning the repo has the snapshot but not your folder."""
        vendorlib.add_local(self.root, self.src, vendor_id="house",
                            license="Proprietary")
        shutil.rmtree(self.src)
        status, detail = vendorlib.sync_one(
            vendorlib.load_upstreams(self.root)[0], self.root)
        self.assertEqual(status, "unchanged")
        self.assertIn("source not on this machine", detail)

    def test_existing_id_is_refused_without_force(self):
        vendorlib.add_local(self.root, self.src, vendor_id="house",
                            license="Proprietary")
        with self.assertRaises(ToolkitError):
            vendorlib.add_local(self.root, self.src, vendor_id="house",
                                license="Proprietary")

    def test_non_directory_is_refused(self):
        with self.assertRaises(ToolkitError):
            vendorlib.add_local(self.root, self.tmp / "nope", vendor_id="x",
                                license="Proprietary")


class TestVendorDeclaration(unittest.TestCase):
    def test_every_vendor_directory_is_declared(self):
        """Undeclared content in vendor/ is invisible to sync, verify and packs."""
        declared = {u.id for u in vendorlib.load_upstreams(ROOT)}
        present = set(vendorlib.vendored_ids(ROOT))
        self.assertEqual(present - declared, set(),
                         "vendor/ holds directories not in catalog/vendor.json")

    def test_no_local_entry_points_outside_the_repo(self):
        """A committed absolute path from one machine breaks every other clone."""
        for up in vendorlib.load_upstreams(ROOT):
            if up.is_local and up.path:
                self.assertFalse(
                    up.path.startswith(("/tmp", "/private/tmp", str(Path.home()))),
                    f"{up.id} points at a machine-specific path: {up.path}",
                )


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
