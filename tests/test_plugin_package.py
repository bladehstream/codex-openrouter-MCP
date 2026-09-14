import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MARKETPLACE_ROOT = ROOT / ".agents" / "plugins"
PLUGIN_ROOT = ROOT / "plugins" / "openrouter-delegator"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "delegate-openrouter"


class PluginPackageTests(unittest.TestCase):
    def test_marketplace_source_resolves_to_plugin(self):
        marketplace = json.loads((MARKETPLACE_ROOT / "marketplace.json").read_text())
        self.assertEqual(marketplace["name"], "codex-openrouter-mcp")
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "openrouter-delegator")
        # Git marketplaces resolve local plugin sources from the installed
        # repository root, not from the marketplace.json parent directory.
        source = (ROOT / entry["source"]["path"]).resolve()
        self.assertEqual(source, PLUGIN_ROOT.resolve())
        self.assertTrue((source / ".codex-plugin" / "plugin.json").is_file())

    def test_manifest_components_exist(self):
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text()
        )
        self.assertEqual(manifest["name"], "openrouter-delegator")
        self.assertTrue((PLUGIN_ROOT / manifest["skills"]).is_dir())
        self.assertTrue((PLUGIN_ROOT / manifest["mcpServers"]).is_file())

    def test_mcp_uses_portable_entrypoint_and_gates_writes(self):
        config = json.loads((PLUGIN_ROOT / ".mcp.json").read_text())
        server = config["mcpServers"]["openrouter_delegator"]
        self.assertEqual(server["command"], "codex-openrouter-mcp")
        self.assertNotIn("cwd", server)
        self.assertEqual(server["env"]["OPENROUTER_ARTIFACT_ROOT_MODE"], "cwd")
        self.assertEqual(server["tools"]["commit_artifact"]["approval_mode"], "prompt")
        self.assertIn("OPENROUTER_API_KEY", server["env_vars"])
        self.assertIn("review_files", server["enabled_tools"])
        self.assertEqual(server["tools"]["review_files"]["output_token_limit"], 16000)

    def test_skill_references_are_bundled(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        self.assertTrue(skill.startswith("---\nname: delegate-openrouter\n"))
        for name in ("routing.md", "artifacts.md", "security.md"):
            self.assertIn(f"references/{name}", skill)
            self.assertTrue((SKILL_ROOT / "references" / name).is_file())

    def test_package_contains_no_scaffold_placeholders(self):
        for path in PLUGIN_ROOT.rglob("*"):
            if path.is_file():
                self.assertNotIn("[TODO:", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
