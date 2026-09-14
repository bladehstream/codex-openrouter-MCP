from __future__ import annotations

import json
import os
import pathlib
import tempfile
import threading
import unittest


from codex_openrouter_delegator import artifacts
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
        for name in (".env", ".ENV.local", "Secrets.toml", "AUTH.JSON", "client.pem"):
            with self.subTest(name=name):
                self.assertTrue(artifacts.is_denied_name(name))

    def test_output_is_top_level_and_inert(self) -> None:
        artifacts.validate_output_name("report.md")
        for name in ("nested/report.md", "script.py", "page.html", "image.svg"):
            with self.subTest(name=name), self.assertRaises(artifacts.ArtifactSecurityError):
                artifacts.validate_output_name(name)

    def test_secret_detection(self) -> None:
        self.assertIsNotNone(artifacts.detect_secret("api_key=sk-exampleexampleexample123"))
        self.assertIsNotNone(artifacts.detect_secret("-----BEGIN PRIVATE KEY-----"))
        self.assertIsNone(artifacts.detect_secret("ordinary design notes"))


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


class ArtifactStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        (self.root / "notes.md").write_text("INPUT_MARKER\n", encoding="utf-8")
        self.store = artifacts.ArtifactStore(self.root, fake_generator)

    def tearDown(self) -> None:
        self.temporary.cleanup()

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
        with self.assertRaises(artifacts.ArtifactSecurityError):
            store.prepare(
                {
                    "profile": "glm_mechanical",
                    "task": "test",
                    "input_paths": ["unsafe.txt"],
                    "outputs": [{"path": "out.md"}],
                }
            )
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
