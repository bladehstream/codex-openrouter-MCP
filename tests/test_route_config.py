from __future__ import annotations

import contextlib
import io
import json
import pathlib
import tempfile
import unittest

from codex_openrouter_delegator import route_config


def valid_payload() -> dict:
    return {
        "version": 1,
        "profiles": {
            "review": {
                "role": "review",
                "model": "vendor/model",
                "instructions": "Review carefully.\nReturn evidence.",
                "reasoning": {"effort": "medium", "exclude": True},
                "providers": [
                    {"slug": "cheap", "display": "Cheap", "weight": 20},
                    {"slug": "fast", "display": "Fast", "weight": 80},
                    {"slug": "stable", "display": "Stable", "weight": 80},
                ],
            }
        },
    }


class RouteConfigTests(unittest.TestCase):
    def test_bundled_config_has_last_resort_deepseek_providers(self) -> None:
        routes, metadata = route_config.load_routes()
        deepseek = routes["deepseek_high"]
        self.assertEqual(
            deepseek.provider_slugs,
            ("fireworks", "relace", "novita", "siliconflow"),
        )
        self.assertEqual(deepseek.provider_weights, (100.0, 90.0, 60.0, 50.0))
        self.assertEqual(metadata["source"], "bundled")
        self.assertEqual(len(metadata["sha256"]), 64)

    def test_weights_sort_descending_and_ties_preserve_file_order(self) -> None:
        route = route_config.validate_routes(valid_payload())["review"]
        self.assertEqual(route.provider_slugs, ("fast", "stable", "cheap"))
        self.assertEqual(route.provider_weights, (80.0, 80.0, 20.0))

    def test_external_file_is_validated_and_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            path = pathlib.Path(raw_dir) / "routes.json"
            path.write_text(json.dumps(valid_payload()), encoding="utf-8")
            routes, metadata = route_config.load_routes(path)
        self.assertIn("review", routes)
        self.assertEqual(metadata["source"], "external")
        self.assertEqual(metadata["path"], str(path.resolve()))

    def test_invalid_weight_duplicate_provider_and_unknown_field_fail(self) -> None:
        cases = []
        invalid_weight = valid_payload()
        invalid_weight["profiles"]["review"]["providers"][0]["weight"] = -1
        cases.append(invalid_weight)
        duplicate = valid_payload()
        duplicate["profiles"]["review"]["providers"][1]["slug"] = "cheap"
        cases.append(duplicate)
        unknown = valid_payload()
        unknown["profiles"]["review"]["unexpected"] = True
        cases.append(unknown)
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(
                route_config.RouteConfigError
            ):
                route_config.validate_routes(payload)

    def test_duplicate_json_keys_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            path = pathlib.Path(raw_dir) / "routes.json"
            path.write_text('{"version":1,"version":1,"profiles":{}}', encoding="utf-8")
            with self.assertRaises(route_config.RouteConfigError):
                route_config.load_routes(path)

    def test_cli_can_print_reusable_default(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(route_config.main(["--show-default"]), 0)
        parsed = json.loads(output.getvalue())
        self.assertEqual(parsed["version"], 1)
        self.assertIn("deepseek_high", parsed["profiles"])

    def test_cli_reports_invalid_configuration_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            path = pathlib.Path(raw_dir) / "routes.json"
            path.write_text("{}", encoding="utf-8")
            errors = io.StringIO()
            with contextlib.redirect_stderr(errors), self.assertRaises(SystemExit) as raised:
                route_config.main([str(path)])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("route configuration error:", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
