from __future__ import annotations

import json
import os
import pathlib
import tempfile
import threading
import time
import unittest
from unittest import mock


from codex_openrouter_delegator import artifacts
from codex_openrouter_delegator import safety
from codex_openrouter_delegator import server as mcp_server


def fake_generator(profile: str, prompt: str, _max_tokens: int) -> dict:
    marker = "INPUT_MARKER" if "INPUT_MARKER" in prompt else "NO_INPUT"
    requested = json.loads(prompt.split("Return exactly these output paths: ", 1)[1].splitlines()[0])
    files = [
        {"path": path, "content": f"# Generated\n\n{marker}\n"}
        for path in requested
    ]
    return {
        "delegation_id": "dlg_fake",
        "requested_model": "fake/model",
        "resolved_model": "fake/model",
        "selected_provider": "Fake",
        "fallback_used": False,
        "elapsed_ms": 1,
        "usage": {"total_tokens": 1},
        "privacy": {"zdr": True, "data_collection": "deny"},
        "result": json.dumps({"files": files}),
    }


class ArtifactPathTests(unittest.TestCase):
    def test_rejects_traversal_absolute_unc_device_ads_and_reserved_names(self) -> None:
        invalid = [
            "../secret.md",
            "/absolute.md",
            "C:/absolute.md",
            "C:relative.md",
            "//server/share.md",
            "//?/C:/device.md",
            "report.md:hidden.exe",
            "CON.md",
            "nul.txt",
            "trailing. ",
            "trailing.",
        ]
        for path in invalid:
            with self.subTest(path=path), self.assertRaises(artifacts.ArtifactSecurityError):
                artifacts.validate_relative_parts(path)

    def test_denies_sensitive_names_case_insensitively(self) -> None:
        for name in (".env", ".ENV.local", "AUTH.JSON", "client.pem"):
            with self.subTest(name=name):
                self.assertTrue(artifacts.is_denied_name(name))
        for source_name in ("secrets.py", "credentials.py"):
            with self.subTest(source_name=source_name):
                self.assertFalse(artifacts.is_denied_name(source_name))

    def test_output_is_top_level_and_inert(self) -> None:
        artifacts.validate_output_name("report.md")
        for name in ("nested/report.md", "script.py", "page.html", "image.svg"):
            with self.subTest(name=name), self.assertRaises(artifacts.ArtifactSecurityError):
                artifacts.validate_output_name(name)

    def test_default_scanner_does_not_block_credential_handling_code(self) -> None:
        safe_code = """
async def refresh(self, token: TokenEnvelope) -> TokenEnvelope: ...
access_token: str
refresh_token: str | None = None
token = _bearer_value(authorization)
notifier.token = payload.publisher_token
ADMIN_TOKEN = os.getenv("INKMETER_ADMIN_TOKEN", "")
NTFY_TOKEN_VAULT_KEY = "ntfy_publisher_token"
"""
        with mock.patch.dict(os.environ, {safety.SCANNER_ENV: ""}, clear=False):
            self.assertIsNone(safety.scan_text(safe_code, source="test.py"))


class ArtifactFormatTests(unittest.TestCase):
    def test_rejects_duplicate_json_keys(self) -> None:
        with self.assertRaises(artifacts.ArtifactSecurityError):
            artifacts.validate_content("data.json", '{"a":1,"a":2}')

    def test_rejects_csv_formula_and_inconsistent_columns(self) -> None:
        with self.assertRaises(artifacts.ArtifactSecurityError):
            artifacts.validate_content("data.csv", "name,value\nitem,=1+1\n")
        with self.assertRaises(artifacts.ArtifactSecurityError):
            artifacts.validate_content("data.csv", "a,b\n1\n")

    def test_rejects_yaml_tags_and_active_links(self) -> None:
        with self.assertRaises(artifacts.ArtifactSecurityError):
            artifacts.validate_content("data.yaml", "value: !!python/object:new:x")
        with self.assertRaises(artifacts.ArtifactSecurityError):
            artifacts.validate_content("report.md", "[open](javascript:alert(1))")

    def test_accepts_safe_formats(self) -> None:
        artifacts.validate_content("data.json", '{"a":1}')
        artifacts.validate_content("data.csv", "a,b\n1,2\n")
        artifacts.validate_content("data.yaml", "a: 1\n")
        artifacts.validate_content("report.md", "# Safe\n")


class ReviewInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.safety_env = mock.patch.dict(
            os.environ, {safety.SCANNER_ENV: ""}, clear=False
        )
        self.safety_env.start()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()
        self.safety_env.stop()

    def test_loads_source_files_with_hash_metadata(self) -> None:
        content = "def example():\n    return 42\n"
        path = self.root / "large.py"
        path.write_text(content, encoding="utf-8")
        raw = path.read_bytes()
        sections, metadata = artifacts.load_review_inputs(self.root, ["large.py"])
        self.assertIn(raw.decode("utf-8"), sections[0])
        self.assertEqual(metadata[0]["path"], "large.py")
        self.assertEqual(metadata[0]["bytes"], len(raw))
        self.assertEqual(len(metadata[0]["sha256"]), 64)

    def test_accepts_common_configuration_extensions(self) -> None:
        names = ["platformio.ini", "service.cfg", "application.conf"]
        for name in names:
            (self.root / name).write_text("setting=value\n", encoding="utf-8")
        _, metadata = artifacts.load_review_inputs(self.root, names)
        self.assertEqual([item["path"] for item in metadata], names)

    def test_default_policy_allows_credential_code_but_rejects_unsafe_inputs(self) -> None:
        (self.root / "secret.py").write_text(
            "api_key=sk-exampleexampleexample123", encoding="utf-8"
        )
        (self.root / "binary.py").write_bytes(b"safe\x00unsafe")
        (self.root / "invalid.py").write_bytes(b"\xff\xfe")
        (self.root / "archive.zip").write_bytes(b"not really a zip")
        _, metadata = artifacts.load_review_inputs(self.root, ["secret.py"])
        self.assertEqual(metadata[0]["path"], "secret.py")
        for name in ("binary.py", "invalid.py", "archive.zip"):
            with self.subTest(name=name), self.assertRaises(
                artifacts.ArtifactSecurityError
            ):
                artifacts.load_review_inputs(self.root, [name])

    def test_path_error_names_rejected_input(self) -> None:
        (self.root / "firmware.zip").write_bytes(b"not really a zip")
        with self.assertRaisesRegex(
            artifacts.ArtifactSecurityError,
            r"firmware\.zip: input extension is not allowed",
        ):
            artifacts.load_review_inputs(self.root, ["firmware.zip"])

    def test_rejects_duplicate_paths(self) -> None:
        (self.root / "same.py").write_text("pass\n", encoding="utf-8")
        with self.assertRaises(artifacts.ArtifactSecurityError):
            artifacts.load_review_inputs(self.root, ["same.py", "SAME.py"])

    def test_accepts_100_files_and_rejects_101(self) -> None:
        names = []
        for index in range(artifacts.MAX_REVIEW_INPUT_FILES):
            name = f"file_{index}.py"
            (self.root / name).write_text(f"value = {index}\n", encoding="utf-8")
            names.append(name)
        _, metadata = artifacts.load_review_inputs(self.root, names)
        self.assertEqual(len(metadata), 100)
        with self.assertRaises(artifacts.ArtifactSecurityError):
            artifacts.load_review_inputs(self.root, names + ["one_too_many.py"])

    def test_enforces_per_file_and_combined_limits(self) -> None:
        (self.root / "oversize.py").write_text(
            "x" * (artifacts.MAX_REVIEW_FILE_BYTES + 1), encoding="utf-8"
        )
        with self.assertRaises(artifacts.ArtifactSecurityError):
            artifacts.load_review_inputs(self.root, ["oversize.py"])

        half = artifacts.MAX_REVIEW_TOTAL_BYTES // 2 + 1
        (self.root / "one.py").write_text("a" * half, encoding="utf-8")
        (self.root / "two.py").write_text("b" * half, encoding="utf-8")
        with self.assertRaises(artifacts.ArtifactSecurityError):
            artifacts.load_review_inputs(self.root, ["one.py", "two.py"])

    def test_review_tool_sends_content_and_returns_audit_metadata(self) -> None:
        content = "export const answer = 42;\n"
        path = self.root / "module.ts"
        path.write_text(content, encoding="utf-8")
        raw = path.read_bytes()
        with mock.patch.dict(
            os.environ,
            {"OPENROUTER_ARTIFACT_ROOT": str(self.root)},
            clear=False,
        ), mock.patch.object(mcp_server, "perform_task") as perform:
            perform.return_value = {
                "result": "No findings.",
                "privacy": {"zdr": True, "data_collection": "deny"},
            }
            response = mcp_server.McpServer().handle(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "review_files",
                        "arguments": {
                            "profile": "deepseek_high",
                            "task": "Review for correctness.",
                            "input_paths": ["module.ts"],
                        },
                    },
                }
            )
        result = response["result"]["structuredContent"]
        self.assertEqual(result["result"], "No findings.")
        self.assertFalse(result["followup_supported"])
        self.assertIn("start_file_review", result["continuation_hint"])
        self.assertEqual(result["inputs"][0]["path"], "module.ts")
        self.assertEqual(result["input_bytes"], len(raw))
        sent_prompt = perform.call_args.args[1]
        self.assertIn(raw.decode("utf-8"), sent_prompt)
        self.assertIn("untrusted data", sent_prompt)
        self.assertEqual(perform.call_args.kwargs["request_timeout"], 330)

    def test_start_file_review_returns_followup_job_with_manifest(self) -> None:
        (self.root / "module.ini").write_text("setting=value\n", encoding="utf-8")
        with mock.patch.dict(
            os.environ,
            {"OPENROUTER_ARTIFACT_ROOT": str(self.root)},
            clear=False,
        ), mock.patch.object(mcp_server, "perform_task") as perform:
            perform.return_value = {"result": "Review complete.", "delegation_id": "dlg_test"}
            mcp = mcp_server.McpServer()
            response = mcp.handle(
                {
                    "jsonrpc": "2.0",
                    "id": 8,
                    "method": "tools/call",
                    "params": {
                        "name": "start_file_review",
                        "arguments": {
                            "profile": "deepseek_high",
                            "task": "Review configuration.",
                            "input_paths": ["module.ini"],
                        },
                    },
                }
            )
            started = response["result"]["structuredContent"]
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                result = mcp.delegator.get_task_result({"job_id": started["job_id"]})
                if result["status"] == "completed":
                    break
                time.sleep(0.01)
            else:
                self.fail("file review did not complete")

        self.assertTrue(started["followup_supported"])
        self.assertEqual(started["job_kind"], "file_review")
        self.assertEqual(started["inputs"][0]["path"], "module.ini")
        self.assertEqual(result["inputs"], started["inputs"])
        self.assertEqual(perform.call_args.kwargs["request_timeout"], 330)


class ArtifactStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.safety_env = mock.patch.dict(
            os.environ, {safety.SCANNER_ENV: ""}, clear=False
        )
        self.safety_env.start()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        (self.root / "notes.md").write_text("INPUT_MARKER\n", encoding="utf-8")
        self.store = artifacts.ArtifactStore(self.root, fake_generator)

    def tearDown(self) -> None:
        self.temporary.cleanup()
        self.safety_env.stop()

    def prepare(self, path: str = "report.md") -> dict:
        return self.store.prepare(
            {
                "profile": "glm_mechanical",
                "task": "Create a short report.",
                "input_paths": ["notes.md"],
                "outputs": [{"path": path, "format": "markdown"}],
            }
        )

    def test_preview_has_no_filesystem_write(self) -> None:
        preview = self.prepare()
        self.assertEqual(preview["status"], "prepared")
        self.assertFalse((self.store.artifact_root / "report.md").exists())
        self.assertIn("INPUT_MARKER", preview["files"][0]["preview"])

    def test_hash_bound_atomic_new_file_commit(self) -> None:
        preview = self.prepare()
        result = self.store.commit(
            {
                "job_id": preview["job_id"],
                "expected_manifest_sha256": preview["manifest_sha256"],
            }
        )
        destination = self.store.artifact_root / "report.md"
        self.assertEqual(result["status"], "committed")
        self.assertIn("INPUT_MARKER", destination.read_text(encoding="utf-8"))
        self.assertEqual(list(self.store.artifact_root.glob("*.tmp")), [])

    def test_hash_mismatch_and_existing_destination_fail_closed(self) -> None:
        preview = self.prepare()
        with self.assertRaises(artifacts.ArtifactSecurityError):
            self.store.commit(
                {"job_id": preview["job_id"], "expected_manifest_sha256": "0" * 64}
            )
        (self.store.artifact_root / "report.md").write_text("existing", encoding="utf-8")
        with self.assertRaises(artifacts.ArtifactSecurityError):
            self.store.commit(
                {
                    "job_id": preview["job_id"],
                    "expected_manifest_sha256": preview["manifest_sha256"],
                }
            )
        self.assertEqual(
            (self.store.artifact_root / "report.md").read_text(encoding="utf-8"),
            "existing",
        )

    def test_discard_never_deletes_a_file(self) -> None:
        preview = self.prepare()
        result = self.store.discard({"job_id": preview["job_id"]})
        self.assertEqual(result["status"], "discarded")
        self.assertFalse((self.store.artifact_root / "report.md").exists())

    def test_unapproved_input_fails_before_model_call(self) -> None:
        calls = []

        def generator(*args):
            calls.append(args)
            return fake_generator(*args)

        store = artifacts.ArtifactStore(self.root, generator)
        for path in ("../outside.md", ".env", "missing.md"):
            with self.subTest(path=path), self.assertRaises(
                (artifacts.ArtifactSecurityError, FileNotFoundError)
            ):
                store.prepare(
                    {
                        "profile": "glm_mechanical",
                        "task": "test",
                        "input_paths": [path],
                        "outputs": [{"path": "out.md"}],
                    }
                )
        self.assertEqual(calls, [])

    def test_secret_input_fails_before_model_call(self) -> None:
        (self.root / "unsafe.txt").write_text(
            "password=long-secret-value", encoding="utf-8"
        )
        calls = []
        store = artifacts.ArtifactStore(self.root, lambda *args: calls.append(args))
        scanner_module = mock.Mock()
        scanner_module.scan_text.side_effect = (
            lambda text, *, source: "test credential" if "password=" in text else None
        )
        with mock.patch.dict(
            os.environ, {safety.SCANNER_ENV: "tests.fake_scanner"}, clear=False
        ), mock.patch.object(
            safety.importlib, "import_module", return_value=scanner_module
        ):
            safety._load_scanner.cache_clear()
            with self.assertRaises(artifacts.ArtifactSecurityError):
                store.prepare(
                    {
                        "profile": "glm_mechanical",
                        "task": "test",
                        "input_paths": ["unsafe.txt"],
                        "outputs": [{"path": "out.md"}],
                    }
                )
            safety._load_scanner.cache_clear()
        self.assertEqual(calls, [])

    def test_concurrent_commit_has_exactly_one_winner(self) -> None:
        preview = self.prepare()
        arguments = {
            "job_id": preview["job_id"],
            "expected_manifest_sha256": preview["manifest_sha256"],
        }
        outcomes = []

        def commit() -> None:
            try:
                self.store.commit(arguments)
                outcomes.append("pass")
            except artifacts.ArtifactSecurityError:
                outcomes.append("blocked")

        threads = [threading.Thread(target=commit) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sorted(outcomes), ["blocked", "pass"])

    def test_symlink_escape_is_rejected_when_supported(self) -> None:
        outside = self.root.parent / f"outside-{os.getpid()}.md"
        outside.write_text("outside", encoding="utf-8")
        link = self.root / "linked.md"
        try:
            try:
                link.symlink_to(outside)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            with self.assertRaises(artifacts.ArtifactSecurityError):
                artifacts.resolve_input_path(self.root, "linked.md")
        finally:
            outside.unlink(missing_ok=True)

    def test_one_bounded_format_repair_is_allowed(self) -> None:
        calls = []

        def repairing_generator(profile, prompt, maximum):
            calls.append(prompt)
            if len(calls) == 1:
                return {"result": "not json"}
            return fake_generator(profile, prompt, maximum)

        store = artifacts.ArtifactStore(self.root, repairing_generator)
        preview = store.prepare(
            {
                "profile": "glm_mechanical",
                "task": "Create a report.",
                "input_paths": ["notes.md"],
                "outputs": [{"path": "repair.md"}],
            }
        )
        self.assertEqual(len(calls), 2)
        self.assertTrue(preview["model"]["format_repair_attempted"])

    def test_second_invalid_format_still_fails_closed(self) -> None:
        calls = []

        def invalid_generator(*_args):
            calls.append(1)
            return {"result": "still not json"}

        store = artifacts.ArtifactStore(self.root, invalid_generator)
        with self.assertRaises(artifacts.ArtifactSecurityError):
            store.prepare(
                {
                    "profile": "glm_mechanical",
                    "task": "Create a report.",
                    "input_paths": ["notes.md"],
                    "outputs": [{"path": "invalid.md"}],
                }
            )
        self.assertEqual(len(calls), 2)
        self.assertFalse((store.artifact_root / "invalid.md").exists())


class ArtifactMcpContractTests(unittest.TestCase):
    def test_commit_is_mutating_and_preview_is_read_only(self) -> None:
        tools = {tool["name"]: tool for tool in mcp_server.tool_definitions()}
        self.assertFalse(tools["commit_artifact"]["annotations"]["readOnlyHint"])
        self.assertTrue(tools["preview_artifact"]["annotations"]["readOnlyHint"])
        self.assertTrue(tools["prepare_artifact"]["annotations"]["readOnlyHint"])

    def test_server_requires_explicit_artifact_root(self) -> None:
        previous = os.environ.pop("OPENROUTER_ARTIFACT_ROOT", None)
        try:
            server = mcp_server.McpServer()
            response = server.handle(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": "list_artifact_jobs", "arguments": {}},
                }
            )
            self.assertIn("OPENROUTER_ARTIFACT_ROOT", response["error"]["message"])
        finally:
            if previous is not None:
                os.environ["OPENROUTER_ARTIFACT_ROOT"] = previous


if __name__ == "__main__":
    unittest.main()
