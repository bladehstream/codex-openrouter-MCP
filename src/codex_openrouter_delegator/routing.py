"""OpenRouter routes, request client, and provider-audit validation."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from typing import Any

from .route_config import Route
from .route_config import load_active_routes


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


ROUTES, ROUTE_CONFIG = load_active_routes()


class RoutingError(RuntimeError):
    pass


def provider_policy(route: Route) -> dict[str, Any]:
    return {
        "only": list(route.allowed_provider_slugs),
        "order": list(route.allowed_provider_slugs),
        "allow_fallbacks": bool(route.fallback_provider_slugs),
        "zdr": True,
        "data_collection": "deny",
        "require_parameters": True,
    }


def request_json(
    key: str,
    body: dict[str, Any],
    *,
    timeout: float = 120,
    transient_retries: int = 0,
) -> dict[str, Any]:
    return _request_endpoint(
        key,
        "responses",
        body,
        timeout=timeout,
        transient_retries=transient_retries,
    )


def request_chat_json(
    key: str,
    body: dict[str, Any],
    *,
    timeout: float = 120,
    transient_retries: int = 0,
) -> dict[str, Any]:
    return _request_endpoint(
        key,
        "chat/completions",
        body,
        timeout=timeout,
        transient_retries=transient_retries,
    )


def _request_endpoint(
    key: str,
    endpoint: str,
    body: dict[str, Any],
    *,
    timeout: float,
    transient_retries: int,
) -> dict[str, Any]:
    encoded = json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-OpenRouter-Metadata": "enabled",
        "HTTP-Referer": "https://local.codex.openrouter.delegator.invalid",
        "X-OpenRouter-Title": "Codex OpenRouter Delegator",
    }
    transient = {429, 502, 503, 529}
    for attempt in range(transient_retries + 1):
        request = urllib.request.Request(
            f"{OPENROUTER_BASE_URL}/{endpoint}",
            data=encoded,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"error": {"message": raw.decode("utf-8", errors="replace")}}
            if exc.code not in transient or attempt == transient_retries:
                raise RoutingError(
                    f"OpenRouter HTTP {exc.code}: {safe_error(payload)}"
                ) from exc
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def output_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    parts: list[str] = []
    for item in payload.get("output", []):
        if (
            not isinstance(item, dict)
            or item.get("type") != "message"
            or item.get("role") != "assistant"
        ):
            continue
        for content in item.get("content", []):
            if (
                isinstance(content, dict)
                and content.get("type") == "output_text"
                and isinstance(content.get("text"), str)
            ):
                parts.append(content["text"])
    return "\n".join(parts)


def chat_output_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    return content if isinstance(content, str) else ""


def selected_providers(payload: dict[str, Any]) -> list[str]:
    metadata = payload.get("openrouter_metadata")
    if not isinstance(metadata, dict):
        return []
    selected: list[str] = []
    endpoints = metadata.get("endpoints")
    if isinstance(endpoints, dict):
        for endpoint in endpoints.get("available", []):
            if isinstance(endpoint, dict) and endpoint.get("selected") is True:
                provider = endpoint.get("provider")
                if isinstance(provider, str):
                    selected.append(provider)
    for attempt in metadata.get("attempts", []):
        if isinstance(attempt, dict) and attempt.get("status") == 200:
            provider = attempt.get("provider")
            if isinstance(provider, str) and provider not in selected:
                selected.append(provider)
    return selected


def validate_response(payload: dict[str, Any], route: Route) -> None:
    model = payload.get("model")
    if not isinstance(model, str):
        raise RoutingError("OpenRouter omitted the resolved model")
    if route.resolved_model_pattern:
        if not re.fullmatch(route.resolved_model_pattern, model, flags=re.IGNORECASE):
            raise RoutingError(f"resolved model does not match approved pattern: {model}")
    elif model != route.model:
        raise RoutingError(f"unexpected resolved model: {model}")
    providers = selected_providers(payload)
    if not providers:
        raise RoutingError("OpenRouter omitted selected-provider metadata")
    allowed = {provider.casefold() for provider in route.allowed_provider_displays}
    if any(provider.casefold() not in allowed for provider in providers):
        raise RoutingError(f"unapproved provider selected: {providers}")


def safe_error(payload: dict[str, Any]) -> str:
    error = payload.get("error")
    message = str(error.get("message", error)) if isinstance(error, dict) else "request failed"
    metadata = payload.get("openrouter_metadata")
    attempts = []
    if isinstance(metadata, dict):
        for attempt in metadata.get("attempts", []):
            if isinstance(attempt, dict):
                attempts.append(
                    {"provider": attempt.get("provider"), "status": attempt.get("status")}
                )
    return f"{message[:300]}; attempts={attempts}"[:700]
