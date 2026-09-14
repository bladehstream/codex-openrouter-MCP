import json
import pathlib
import re
import tomllib
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

    def test_runtime_plugin_and_project_versions_match(self):
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text()
        )
        config = json.loads((PLUGIN_ROOT / ".mcp.json").read_text())
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        project_version = project["project"]["version"]
        plugin_base_version = manifest["version"].split("+", 1)[0]
        configured_version = config["mcpServers"]["openrouter_delegator"]["env"][
            "OPENROUTER_PLUGIN_BASE_VERSION"
        ]
        self.assertEqual(plugin_base_version, project_version)
        self.assertEqual(configured_version, project_version)

    def test_mcp_uses_portable_entrypoint_and_gates_writes(self):
        config = json.loads((PLUGIN_ROOT / ".mcp.json").read_text())
        server = config["mcpServers"]["openrouter_delegator"]
        self.assertEqual(server["command"], "codex-openrouter-mcp")
        self.assertNotIn("cwd", server)
        self.assertEqual(server["env"]["OPENROUTER_ARTIFACT_ROOT_MODE"], "cwd")
        self.assertEqual(server["tools"]["commit_artifact"]["approval_mode"], "prompt")
        self.assertIn("OPENROUTER_API_KEY", server["env_vars"])
        self.assertIn("OPENROUTER_SAFETY_SCANNER_MODULE", server["env_vars"])
        self.assertIn("review_files", server["enabled_tools"])
        self.assertIn("start_file_review", server["enabled_tools"])
        self.assertEqual(server["tools"]["review_files"]["output_token_limit"], 16000)
        self.assertEqual(server["env"]["OPENROUTER_PLUGIN_BASE_VERSION"], "0.3.0")

    def test_skill_references_are_bundled(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        self.assertTrue(skill.startswith("---\nname: delegate-openrouter\n"))
        for name in ("routing.md", "artifacts.md", "security.md", "continuation.md"):
            self.assertIn(f"references/{name}", skill)
            self.assertTrue((SKILL_ROOT / "references" / name).is_file())

    def test_package_contains_no_scaffold_placeholders(self):
        for path in PLUGIN_ROOT.rglob("*"):
            if path.is_file():
                self.assertNotIn("[TODO:", path.read_text(encoding="utf-8"))

    def test_documentation_relative_links_resolve(self):
        markdown_files = [ROOT / "README.md", ROOT / "SECURITY.md"]
        markdown_files.extend((ROOT / "docs").glob("*.md"))
        markdown_files.extend((PLUGIN_ROOT / "skills").rglob("*.md"))
        link_pattern = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
        missing = []
        for document in markdown_files:
            for target in link_pattern.findall(document.read_text(encoding="utf-8")):
                path_text = target.split("#", 1)[0]
                if not path_text or "://" in path_text or path_text.startswith("mailto:"):
                    continue
                resolved = (document.parent / path_text).resolve()
                if not resolved.exists():
                    missing.append(f"{document.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
