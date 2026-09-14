from __future__ import annotations

import time
import unittest
from unittest import mock

from codex_openrouter_delegator import server


class JobTests(unittest.TestCase):
    def test_async_status_cancel_and_limits(self) -> None:
        delegator = server.Delegator()

        def slow_result(profile, task, max_tokens, **_kwargs):
            time.sleep(0.2)
            return {
                "profile": profile,
                "result": task,
                "delegation_id": "dlg_test",
                "usage": {"total_tokens": max_tokens},
            }

        with mock.patch.object(server, "perform_task", side_effect=slow_result):
            started = delegator.start_task(
                {"profile": "glm_mechanical", "task": "test", "max_output_tokens": 32}
            )
            status = delegator.get_task_status({"job_id": started["job_id"]})
            self.assertIn(status["status"], {"queued", "running"})
            cancelled = delegator.cancel_task({"job_id": started["job_id"]})
            self.assertIn(cancelled["status"], {"cancelled", "cancel_requested"})

    def test_output_limit_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            server.validate_task_arguments(
                {"profile": "glm_mechanical", "task": "x", "max_output_tokens": 12_001}
            )

    def test_large_inline_task_limit(self) -> None:
        profile, task, maximum = server.validate_task_arguments(
            {"profile": "deepseek_high", "task": "x" * 200_000}
        )
        self.assertEqual(profile, "deepseek_high")
        self.assertEqual(len(task), 200_000)
        self.assertEqual(maximum, 1200)
        with self.assertRaises(ValueError):
            server.validate_task_arguments(
                {"profile": "deepseek_high", "task": "x" * 200_001}
            )

    def test_followup_preserves_full_initial_context(self) -> None:
        delegator = server.Delegator()
        initial = "BEGIN\n" + ("x" * 13_000) + "\nTAIL_MARKER"
        calls = []

        def result(profile, task, max_tokens, **_kwargs):
            calls.append(task)
            return {
                "profile": profile,
                "result": "FIRST_RESULT" if len(calls) == 1 else "SECOND_RESULT",
                "delegation_id": f"dlg_{len(calls)}",
                "usage": {"total_tokens": max_tokens},
            }

        with mock.patch.object(server, "perform_task", side_effect=result):
            started = delegator.start_prepared_task(
                "deepseek_high",
                initial,
                64,
                kind="file_review",
                metadata={"inputs": [{"path": "large.py", "sha256": "a" * 64}]},
            )
            self._wait_completed(delegator, started["job_id"])
            delegator.send_followup(
                {"job_id": started["job_id"], "message": "FOCUSED_FOLLOWUP"}
            )
            self._wait_completed(delegator, started["job_id"])
            completed = delegator.get_task_result({"job_id": started["job_id"]})

        self.assertIn("TAIL_MARKER", calls[1])
        self.assertIn("FIRST_RESULT", calls[1])
        self.assertIn("FOCUSED_FOLLOWUP", calls[1])
        self.assertEqual(completed["job_kind"], "file_review")
        self.assertTrue(completed["followup_supported"])
        self.assertEqual(completed["inputs"][0]["path"], "large.py")

    def test_reasoning_only_response_gets_one_bounded_finalization(self) -> None:
        route = server.PROFILES["deepseek_high"]
        metadata = {
            "endpoints": {"available": [{"provider": "Fireworks", "selected": True}]}
        }
        reasoning_only = {
            "model": route.model,
            "output": [
                {
                    "type": "reasoning",
                    "content": [{"type": "summary_text", "text": "scratch"}],
                }
            ],
            "usage": {
                "output_tokens": 100,
                "output_tokens_details": {"reasoning_tokens": 100},
            },
            "openrouter_metadata": metadata,
        }
        finalized = {
            "model": route.model,
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "final answer"}],
                }
            ],
            "usage": {"output_tokens": 20},
            "openrouter_metadata": metadata,
        }
        with mock.patch.object(
            server.credentials, "load_openrouter_key", return_value="hidden"
        ), mock.patch.object(
            server.routing, "request_json", side_effect=[reasoning_only, finalized]
        ) as request:
            result = server.perform_task("deepseek_high", "analyze", 12_000)

        self.assertEqual(result["result"], "final answer")
        self.assertTrue(result["finalization_attempted"])
        self.assertEqual(result["attempt_count"], 2)
        self.assertEqual(result["usage"]["reasoning_tokens"], 100)
        self.assertEqual(result["usage"]["output_tokens"], 120)
        first_body = request.call_args_list[0].args[1]
        final_body = request.call_args_list[1].args[1]
        self.assertEqual(first_body["reasoning"], {"effort": "low", "exclude": True})
        self.assertEqual(final_body["reasoning"], {"effort": "none", "exclude": True})
        self.assertEqual(final_body["max_output_tokens"], 4000)

    @staticmethod
    def _wait_completed(delegator: server.Delegator, job_id: str) -> None:
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            status = delegator.get_task_status({"job_id": job_id})["status"]
            if status == "completed":
                return
            if status in {"failed", "cancelled"}:
                raise AssertionError(status)
            time.sleep(0.01)
        raise AssertionError("job did not complete")


if __name__ == "__main__":
    unittest.main()
