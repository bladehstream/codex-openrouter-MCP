from __future__ import annotations

import time
import unittest
from unittest import mock

from codex_openrouter_delegator import server


class JobTests(unittest.TestCase):
    def test_async_status_cancel_and_limits(self) -> None:
        delegator = server.Delegator()

        def slow_result(profile, task, max_tokens):
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


if __name__ == "__main__":
    unittest.main()
