from __future__ import annotations

import os
import pathlib
import tempfile
import unittest
from unittest import mock

from codex_openrouter_delegator import server
from codex_openrouter_delegator import safety


class McpProtocolTests(unittest.TestCase):
    def test_initialize_and_catalog(self) -> None:
        mcp = server.McpServer()
        initialized = mcp.handle(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
        )
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(initialized["result"]["serverInfo"]["version"], "0.4.0")
        listed = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = {tool["name"]: tool for tool in listed["result"]["tools"]}
        self.assertEqual(len(tools), 14)
        self.assertFalse(tools["commit_artifact"]["annotations"]["readOnlyHint"])
        self.assertTrue(tools["preview_artifact"]["annotations"]["readOnlyHint"])
        self.assertTrue(tools["review_files"]["annotations"]["readOnlyHint"])
        self.assertTrue(tools["start_file_review"]["annotations"]["readOnlyHint"])
        self.assertEqual(
            tools["delegate_task"]["inputSchema"]["properties"]["task"]["maxLength"],
            200_000,
        )
        self.assertEqual(
            tools["review_files"]["inputSchema"]["properties"]["input_paths"]["maxItems"],
            100,
        )

    def test_unknown_profile_fails_before_network(self) -> None:
        mcp = server.McpServer()
        response = mcp.handle(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "delegate_task",
                    "arguments": {"profile": "unknown", "task": "test"},
                },
            }
        )
        self.assertIn("unknown profile", response["error"]["message"])

    def test_profile_catalog_discloses_local_scanner_status(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                safety.SCANNER_ENV: "",
                safety.EXPECTED_GUARDRAIL_ENV: "expected-policy",
                "OPENROUTER_PLUGIN_BASE_VERSION": "0.4.0",
            },
            clear=False,
        ):
            catalog = server.Delegator().list_profiles()
        self.assertFalse(catalog["input_safety"]["local_scanner_enabled"])
        self.assertIn("OpenRouter", catalog["input_safety"]["boundary"])
        self.assertEqual(
            catalog["input_safety"]["guardrail_status"], "configured_unverified"
        )
        self.assertEqual(catalog["runtime"]["server_version"], "0.4.0")
        self.assertTrue(catalog["runtime"]["versions_match"])
        deepseek = next(
            profile
            for profile in catalog["profiles"]
            if profile["id"] == "deepseek_high"
        )
        self.assertEqual(
            [provider["weight"] for provider in deepseek["provider_preferences"]],
            [100.0, 90.0, 60.0, 50.0],
        )
        self.assertEqual(len(catalog["route_config"]["sha256"]), 64)

    def test_cwd_root_mode_is_explicit_and_rejects_home(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir, mock.patch.dict(
            os.environ,
            {"OPENROUTER_ARTIFACT_ROOT_MODE": "cwd", "OPENROUTER_ARTIFACT_ROOT": ""},
            clear=False,
        ), mock.patch.object(server.pathlib.Path, "cwd", return_value=pathlib.Path(raw_dir)):
            self.assertEqual(server.configured_artifact_root(), pathlib.Path(raw_dir).resolve())


if __name__ == "__main__":
    unittest.main()
