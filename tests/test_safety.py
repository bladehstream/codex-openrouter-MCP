from __future__ import annotations

import os
import unittest
from unittest import mock

from codex_openrouter_delegator import safety
from codex_openrouter_delegator import server


class SafetyScannerTests(unittest.TestCase):
    def tearDown(self) -> None:
        safety._load_scanner.cache_clear()

    def test_disabled_by_default(self) -> None:
        with mock.patch.dict(os.environ, {safety.SCANNER_ENV: ""}, clear=False):
            self.assertIsNone(safety.scan_text("password=literal-value", source="input"))
            status = safety.status()
        self.assertFalse(status["local_scanner_enabled"])
        self.assertIsNone(status["local_scanner_module"])

    def test_configured_module_receives_text_and_source(self) -> None:
        module = mock.Mock()
        module.scan_text.return_value = "company policy match"
        with mock.patch.dict(
            os.environ, {safety.SCANNER_ENV: "company.scanner"}, clear=False
        ), mock.patch.object(safety.importlib, "import_module", return_value=module):
            result = safety.scan_text("sensitive", source="review-input:app.py")
            status = safety.status()
        self.assertEqual(result, "company policy match")
        module.scan_text.assert_called_once_with(
            "sensitive", source="review-input:app.py"
        )
        self.assertTrue(status["local_scanner_enabled"])
        self.assertEqual(status["local_scanner_module"], "company.scanner")

    def test_configured_scanner_failures_are_closed(self) -> None:
        with mock.patch.dict(
            os.environ, {safety.SCANNER_ENV: "missing.scanner"}, clear=False
        ), mock.patch.object(
            safety.importlib, "import_module", side_effect=ImportError("missing")
        ):
            with self.assertRaises(safety.SafetyScannerError):
                safety.scan_text("content", source="input")

    def test_invalid_scanner_result_is_rejected(self) -> None:
        module = mock.Mock()
        module.scan_text.return_value = False
        with mock.patch.dict(
            os.environ, {safety.SCANNER_ENV: "company.scanner"}, clear=False
        ), mock.patch.object(safety.importlib, "import_module", return_value=module):
            with self.assertRaises(safety.SafetyScannerError):
                safety.scan_text("content", source="input")

    def test_scanner_finding_cannot_echo_long_or_multiline_content(self) -> None:
        module = mock.Mock()
        with mock.patch.dict(
            os.environ, {safety.SCANNER_ENV: "company.scanner"}, clear=False
        ), mock.patch.object(safety.importlib, "import_module", return_value=module):
            for unsafe_finding in ("x" * 201, "line one\nline two"):
                with self.subTest(unsafe_finding=unsafe_finding):
                    module.scan_text.return_value = unsafe_finding
                    with self.assertRaises(safety.SafetyScannerError):
                        safety.scan_text("content", source="input")

    def test_inline_delegation_is_scanned_before_credentials_or_network(self) -> None:
        with mock.patch.object(
            server.safety, "scan_text", return_value="company policy match"
        ), mock.patch.object(server.credentials, "load_openrouter_key") as load_key:
            with self.assertRaisesRegex(ValueError, "local safety scanner"):
                server.perform_task("glm_mechanical", "blocked content", 32)
        load_key.assert_not_called()


if __name__ == "__main__":
    unittest.main()
