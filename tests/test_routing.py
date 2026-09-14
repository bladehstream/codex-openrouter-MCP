from __future__ import annotations

import unittest

from codex_openrouter_delegator import routing


class RoutingTests(unittest.TestCase):
    def test_profiles_are_exact(self) -> None:
        deepseek = routing.ROUTES["deepseek_high"]
        glm = routing.ROUTES["glm_mechanical"]
        self.assertEqual(deepseek.model, "deepseek/deepseek-v4.1-flash")
        self.assertEqual(deepseek.allowed_provider_slugs, ("fireworks", "relace"))
        self.assertEqual(glm.model, "~z-ai/glm-flash-latest")
        self.assertEqual(glm.allowed_provider_slugs, ("relace", "wafer"))

    def test_provider_policy_is_closed_and_private(self) -> None:
        for route in routing.ROUTES.values():
            policy = routing.provider_policy(route)
            self.assertEqual(policy["only"], list(route.allowed_provider_slugs))
            self.assertEqual(policy["order"], list(route.allowed_provider_slugs))
            self.assertTrue(policy["allow_fallbacks"])
            self.assertTrue(policy["zdr"])
            self.assertEqual(policy["data_collection"], "deny")
            self.assertTrue(policy["require_parameters"])

    def test_response_rejects_unapproved_provider(self) -> None:
        payload = {
            "model": "deepseek/deepseek-v4.1-flash",
            "openrouter_metadata": {
                "endpoints": {
                    "available": [{"provider": "Unapproved", "selected": True}]
                }
            },
        }
        with self.assertRaises(routing.RoutingError):
            routing.validate_response(payload, routing.ROUTES["deepseek_high"])

    def test_glm_alias_accepts_only_glm_flash_family(self) -> None:
        route = routing.ROUTES["glm_mechanical"]
        valid = {
            "model": "z-ai/glm-5.3-flash",
            "openrouter_metadata": {
                "endpoints": {"available": [{"provider": "Relace", "selected": True}]}
            },
        }
        routing.validate_response(valid, route)
        invalid = {**valid, "model": "z-ai/glm-5.3"}
        with self.assertRaises(routing.RoutingError):
            routing.validate_response(invalid, route)

    def test_chat_output_text(self) -> None:
        payload = {"choices": [{"message": {"content": '{"ok":true}'}}]}
        self.assertEqual(routing.chat_output_text(payload), '{"ok":true}')


if __name__ == "__main__":
    unittest.main()
