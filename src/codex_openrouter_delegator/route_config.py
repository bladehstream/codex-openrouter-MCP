"""Validated, versioned model and provider profile configuration."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.resources
import json
import os
import pathlib
import re
from typing import Any


ROUTES_FILE_ENV = "OPENROUTER_ROUTES_FILE"
CONFIG_VERSION = 1
MAX_CONFIG_BYTES = 1_000_000
PROFILE_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
MODEL_NAME = re.compile(r"^~?[A-Za-z0-9._:-]+/[A-Za-z0-9._:~-]+$")
PROVIDER_SLUG = re.compile(r"^[a-z0-9]+(?:[a-z0-9_./-]*[a-z0-9])?$")
REASONING_EFFORTS = {"max", "xhigh", "high", "medium", "low", "minimal", "none"}


class RouteConfigError(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class Route:
    role: str
    model: str
    instructions: str
    provider_slugs: tuple[str, ...]
    provider_displays: tuple[str, ...]
    provider_weights: tuple[float, ...]
    reasoning: dict[str, Any]
    resolved_model_pattern: str | None = None

    @property
    def provider_slug(self) -> str:
        return self.provider_slugs[0]

    @property
    def provider_display(self) -> str:
        return self.provider_displays[0]

    @property
    def fallback_provider_slugs(self) -> tuple[str, ...]:
        return self.provider_slugs[1:]

    @property
    def fallback_provider_displays(self) -> tuple[str, ...]:
        return self.provider_displays[1:]

    @property
    def allowed_provider_slugs(self) -> tuple[str, ...]:
        return self.provider_slugs

    @property
    def allowed_provider_displays(self) -> tuple[str, ...]:
        return self.provider_displays


def load_active_routes() -> tuple[dict[str, Route], dict[str, Any]]:
    configured = os.environ.get(ROUTES_FILE_ENV, "").strip()
    return load_routes(pathlib.Path(configured)) if configured else load_routes()


def load_routes(
    path: pathlib.Path | None = None,
) -> tuple[dict[str, Route], dict[str, Any]]:
    if path is None:
        raw = (
            importlib.resources.files("codex_openrouter_delegator")
            .joinpath("default_routes.json")
            .read_bytes()
        )
        source = "bundled"
        source_path = None
    else:
        resolved = path.expanduser().resolve(strict=True)
        if not resolved.is_file():
            raise RouteConfigError("route configuration is not a regular file")
        raw = resolved.read_bytes()
        source = "external"
        source_path = str(resolved)
    if len(raw) > MAX_CONFIG_BYTES:
        raise RouteConfigError(f"route configuration exceeds {MAX_CONFIG_BYTES} bytes")
    try:
        text = raw.decode("utf-8", errors="strict")
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except UnicodeDecodeError as exc:
        raise RouteConfigError("route configuration must be UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise RouteConfigError(f"invalid route configuration JSON: line {exc.lineno}") from exc
    routes = validate_routes(payload)
    metadata = {
        "version": CONFIG_VERSION,
        "source": source,
        "path": source_path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "profile_count": len(routes),
    }
    return routes, metadata


def validate_routes(payload: object) -> dict[str, Route]:
    if not isinstance(payload, dict) or set(payload) != {"version", "profiles"}:
        raise RouteConfigError("route configuration needs only version and profiles")
    if payload.get("version") != CONFIG_VERSION:
        raise RouteConfigError(f"route configuration version must be {CONFIG_VERSION}")
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or not 1 <= len(profiles) <= 16:
        raise RouteConfigError("profiles must contain between 1 and 16 entries")
    routes: dict[str, Route] = {}
    for profile, raw_route in profiles.items():
        if not isinstance(profile, str) or not PROFILE_NAME.fullmatch(profile):
            raise RouteConfigError(f"invalid profile name: {profile!r}")
        routes[profile] = _validate_route(profile, raw_route)
    return routes


def _validate_route(profile: str, value: object) -> Route:
    allowed_keys = {
        "role",
        "model",
        "instructions",
        "providers",
        "reasoning",
        "resolved_model_pattern",
    }
    if not isinstance(value, dict) or set(value) - allowed_keys:
        raise RouteConfigError(f"{profile}: route contains unsupported fields")
    role = _bounded_text(value.get("role"), f"{profile}.role", 100)
    model = _bounded_text(value.get("model"), f"{profile}.model", 200)
    if not MODEL_NAME.fullmatch(model):
        raise RouteConfigError(f"{profile}: invalid model slug")
    instructions = _bounded_text(
        value.get("instructions"),
        f"{profile}.instructions",
        4000,
        single_line=False,
    )
    providers = value.get("providers")
    if not isinstance(providers, list) or not 1 <= len(providers) <= 8:
        raise RouteConfigError(f"{profile}: providers must contain between 1 and 8 entries")
    provider_rows: list[tuple[int, str, str, float]] = []
    for index, provider in enumerate(providers):
        if not isinstance(provider, dict) or set(provider) != {"slug", "display", "weight"}:
            raise RouteConfigError(
                f"{profile}.providers[{index}]: expected slug, display, and weight"
            )
        slug = _bounded_text(provider.get("slug"), "provider slug", 100)
        display = _bounded_text(provider.get("display"), "provider display", 100)
        weight = provider.get("weight")
        if (
            not isinstance(weight, (int, float))
            or isinstance(weight, bool)
            or not 0 <= weight <= 1000
        ):
            raise RouteConfigError(f"{profile}: provider weight must be between 0 and 1000")
        if not PROVIDER_SLUG.fullmatch(slug):
            raise RouteConfigError(f"{profile}: invalid provider slug {slug!r}")
        provider_rows.append((index, slug, display, float(weight)))
    provider_rows.sort(key=lambda row: (-row[3], row[0]))
    slugs = [row[1] for row in provider_rows]
    displays = [row[2] for row in provider_rows]
    weights = [row[3] for row in provider_rows]
    if len({slug.casefold() for slug in slugs}) != len(slugs):
        raise RouteConfigError(f"{profile}: provider slugs must be unique")
    if len({display.casefold() for display in displays}) != len(displays):
        raise RouteConfigError(f"{profile}: provider displays must be unique")
    reasoning = value.get("reasoning", {})
    if not isinstance(reasoning, dict) or set(reasoning) - {"effort", "exclude"}:
        raise RouteConfigError(f"{profile}: invalid reasoning configuration")
    effort = reasoning.get("effort", "none")
    exclude = reasoning.get("exclude", True)
    if effort not in REASONING_EFFORTS or not isinstance(exclude, bool):
        raise RouteConfigError(f"{profile}: invalid reasoning effort or exclude value")
    pattern = value.get("resolved_model_pattern")
    if pattern is not None:
        pattern = _bounded_text(pattern, f"{profile}.resolved_model_pattern", 300)
        try:
            re.compile(pattern)
        except re.error as exc:
            raise RouteConfigError(f"{profile}: invalid resolved model pattern") from exc
    return Route(
        role=role,
        model=model,
        instructions=instructions,
        provider_slugs=tuple(slugs),
        provider_displays=tuple(displays),
        provider_weights=tuple(weights),
        reasoning={"effort": effort, "exclude": exclude},
        resolved_model_pattern=pattern,
    )


def _bounded_text(
    value: object, name: str, maximum: int, *, single_line: bool = True
) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise RouteConfigError(f"{name} must be a non-empty string up to {maximum} characters")
    if "\x00" in value or (single_line and any(character in value for character in "\r\n")):
        boundary = "a single line without NUL" if single_line else "free of NUL"
        raise RouteConfigError(f"{name} must be {boundary}")
    return value.strip()


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RouteConfigError(f"duplicate route configuration key: {key}")
        result[key] = value
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate OpenRouter delegation routes")
    parser.add_argument("path", nargs="?", type=pathlib.Path)
    parser.add_argument(
        "--show-default",
        action="store_true",
        help="print the bundled route configuration JSON",
    )
    args = parser.parse_args(argv)
    if args.show_default:
        if args.path is not None:
            parser.error("path cannot be combined with --show-default")
        print(
            importlib.resources.files("codex_openrouter_delegator")
            .joinpath("default_routes.json")
            .read_text(encoding="utf-8"),
            end="",
        )
        return 0
    try:
        routes, metadata = load_routes(args.path)
    except (OSError, RouteConfigError) as exc:
        parser.exit(2, f"route configuration error: {exc}\n")
    summary = {
        "config": metadata,
        "profiles": {
            name: {
                "model": route.model,
                "providers": [
                    {"slug": slug, "display": display, "weight": weight}
                    for slug, display, weight in zip(
                        route.provider_slugs,
                        route.provider_displays,
                        route.provider_weights,
                        strict=True,
                    )
                ],
            }
            for name, route in routes.items()
        },
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
