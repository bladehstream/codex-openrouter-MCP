from __future__ import annotations

import os
import pathlib
import tempfile
import unittest
from unittest import mock

from codex_openrouter_delegator import server


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
        listed = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = {tool["name"]: tool for tool in listed["result"]["tools"]}
        self.assertEqual(len(tools), 12)
        self.assertFalse(tools["commit_artifact"]["annotations"]["readOnlyHint"])
        self.assertTrue(tools["preview_artifact"]["annotations"]["readOnlyHint"])

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

    def test_cwd_root_mode_is_explicit_and_rejects_home(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir, mock.patch.dict(
            os.environ,
            {"OPENROUTER_ARTIFACT_ROOT_MODE": "cwd", "OPENROUTER_ARTIFACT_ROOT": ""},
            clear=False,
        ), mock.patch.object(server.pathlib.Path, "cwd", return_value=pathlib.Path(raw_dir)):
            self.assertEqual(server.configured_artifact_root(), pathlib.Path(raw_dir).resolve())


if __name__ == "__main__":
    unittest.main()
