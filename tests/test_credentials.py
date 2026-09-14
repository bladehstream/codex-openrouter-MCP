from __future__ import annotations

import os
import pathlib
import subprocess
import unittest
from unittest import mock

from codex_openrouter_delegator import credentials


class CredentialTests(unittest.TestCase):
    def test_powershell_get_uses_pipeline_output_not_direct_console(self) -> None:
        script = pathlib.Path(__file__).parents[1] / "scripts" / "openrouter_credential.ps1"
        text = script.read_text(encoding="utf-8")
        self.assertNotIn("[Console]::Out", text)
        self.assertIn("Write-Output $value", text)

    def test_environment_key_for_headless_hosts(self) -> None:
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            self.assertEqual(credentials.load_openrouter_key(), "test-key")

    def test_macos_uses_keychain(self) -> None:
        completed = subprocess.CompletedProcess([], 0, "mac-key\n", "")
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            credentials.platform, "system", return_value="Darwin"
        ), mock.patch.object(credentials.subprocess, "run", return_value=completed) as run:
            self.assertEqual(credentials.load_openrouter_key(), "mac-key")
            self.assertEqual(run.call_args.args[0][0], "/usr/bin/security")

    def test_linux_uses_secret_service(self) -> None:
        completed = subprocess.CompletedProcess([], 0, "linux-key\n", "")
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            credentials.platform, "system", return_value="Linux"
        ), mock.patch.object(credentials.subprocess, "run", return_value=completed) as run:
            self.assertEqual(credentials.load_openrouter_key(), "linux-key")
            self.assertEqual(run.call_args.args[0][0], "secret-tool")


if __name__ == "__main__":
    unittest.main()
