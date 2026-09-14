#!/usr/bin/env python3
"""Paid live acceptance tests. Not executed by ordinary CI."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import queue
import secrets
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any

from codex_openrouter_delegator import credentials


class McpClient:
    def __init__(self, env: dict[str, str] | None = None) -> None:
        environment = os.environ.copy()
        environment.update(env or {})
        self.process = subprocess.Popen(
            [sys.executable, "-m", "codex_openrouter_delegator"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=environment,
        )
        self.messages: queue.Queue[dict[str, Any]] = queue.Queue()
        self.stderr: list[str] = []
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()
        self.next_id = 1
        self.call(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "live-acceptance", "version": "0.1.0"},
            },
        )
        self.notify("notifications/initialized")

    def _read_stdout(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            try:
                self.messages.put(json.loads(line))
            except json.JSONDecodeError:
                continue

    def _read_stderr(self) -> None:
        assert self.process.stderr is not None
        for line in self.process.stderr:
            self.stderr.append(line.rstrip())
            if len(self.stderr) > 100:
                del self.stderr[:-100]

    def notify(self, method: str) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.process.stdin.flush()

    def call(
        self, method: str, params: dict[str, Any] | None = None, timeout: int = 360
    ) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        request = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            request["params"] = params
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
        self.process.stdin.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                response = self.messages.get(timeout=1)
            except queue.Empty:
                if self.process.poll() is not None:
                    raise RuntimeError("MCP server exited: " + "\n".join(self.stderr[-20:]))
                continue
            if response.get("id") != request_id:
                continue
            if "error" in response:
                raise RuntimeError(response["error"]["message"])
            return response["result"]
        raise TimeoutError(method)

    def tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.call(
            "tools/call", {"name": name, "arguments": arguments or {}}
        )["structuredContent"]

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def __enter__(self) -> "McpClient":
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()


def wait_job(client: McpClient, job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        status = client.tool("get_task_status", {"job_id": job_id})
        if status["status"] in {"completed", "failed", "cancelled"}:
            return status
        time.sleep(0.25)
    raise TimeoutError(job_id)


def test_delegation() -> None:
    with McpClient() as client:
        for profile, providers in (
            ("glm_mechanical", {"Relace", "Wafer"}),
            ("deepseek_high", {"Fireworks", "Relace"}),
        ):
            marker = f"LIVE_{profile.upper()}_{secrets.token_hex(5)}"
            result = client.tool(
                "delegate_task",
                {
                    "profile": profile,
                    "task": f"Return exactly {marker} and nothing else.",
                    "max_output_tokens": 96,
                },
            )
            assert marker in result["result"]
            assert result["selected_provider"] in providers
            assert result["privacy"] == {"zdr": True, "data_collection": "deny"}


def test_async_followup() -> None:
    with McpClient() as client:
        first = f"FIRST_{secrets.token_hex(5)}"
        second = f"SECOND_{secrets.token_hex(5)}"
        started = client.tool(
            "start_task",
            {
                "profile": "glm_mechanical",
                "task": f"Return exactly {first}.",
                "max_output_tokens": 96,
            },
        )
        assert wait_job(client, started["job_id"])["status"] == "completed"
        client.tool(
            "send_followup",
            {
                "job_id": started["job_id"],
                "message": f"Return {first} and {second}.",
            },
        )
        assert wait_job(client, started["job_id"])["status"] == "completed"
        result = client.tool("get_task_result", {"job_id": started["job_id"]})
        assert first in result["result"] and second in result["result"]


def test_artifacts() -> None:
    with tempfile.TemporaryDirectory() as raw_dir:
        root = pathlib.Path(raw_dir)
        (root / "brief.md").write_text("Summarize backup and restore verification.\n")
        marker = f"ARTIFACT_{secrets.token_hex(5)}"
        with McpClient({"OPENROUTER_ARTIFACT_ROOT": str(root)}) as client:
            preview = client.tool(
                "prepare_artifact",
                {
                    "profile": "glm_mechanical",
                    "task": f"Create a two-item checklist containing exact marker {marker}.",
                    "input_paths": ["brief.md"],
                    "outputs": [{"path": "checklist.md", "format": "markdown"}],
                },
            )
            destination = root / "artifacts" / "openrouter" / "checklist.md"
            assert not destination.exists()
            assert marker in preview["files"][0]["preview"]
            client.tool(
                "commit_artifact",
                {
                    "job_id": preview["job_id"],
                    "expected_manifest_sha256": preview["manifest_sha256"],
                },
            )
            assert marker in destination.read_text()


def test_large_file_review() -> None:
    with tempfile.TemporaryDirectory() as raw_dir:
        root = pathlib.Path(raw_dir)
        marker = f"LARGE_REVIEW_{secrets.token_hex(5)}"
        content = ("# deterministic review padding\n" * 2200) + f"# marker: {marker}\n"
        source = root / "large.py"
        source.write_text(content, encoding="utf-8")
        assert source.stat().st_size > 40_000
        with McpClient({"OPENROUTER_ARTIFACT_ROOT": str(root)}) as client:
            result = client.tool(
                "review_files",
                {
                    "profile": "glm_mechanical",
                    "task": "Return exactly the marker found in the final line and nothing else.",
                    "input_paths": ["large.py"],
                    "max_output_tokens": 96,
                },
            )
            assert marker in result["result"]
            assert result["input_bytes"] == source.stat().st_size
            assert result["inputs"][0]["path"] == "large.py"
            assert result["selected_provider"] in {"Relace", "Wafer"}
            assert result["privacy"] == {"zdr": True, "data_collection": "deny"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    key = credentials.load_openrouter_key()
    print(f"Credential: present ({len(key)} characters; value hidden)")
    for name, function in (
        ("synchronous delegation", test_delegation),
        ("async follow-up", test_async_followup),
        ("artifact boundary", test_artifacts),
        ("large selected-file review", test_large_file_review),
    ):
        started = time.monotonic()
        print(f"[RUN ] {name}", flush=True)
        function()
        print(f"[PASS] {name} ({time.monotonic() - started:.1f}s)", flush=True)
    print("Live acceptance passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
