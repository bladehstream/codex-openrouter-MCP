"""Optional user-supplied local content scanner boundary."""

from __future__ import annotations

import functools
import importlib
import os
from types import ModuleType
from typing import Callable


SCANNER_ENV = "OPENROUTER_SAFETY_SCANNER_MODULE"
Scanner = Callable[..., str | None]


class SafetyScannerError(RuntimeError):
    pass


def status() -> dict[str, object]:
    module_name = os.environ.get(SCANNER_ENV, "").strip()
    return {
        "local_scanner_enabled": bool(module_name),
        "local_scanner_module": module_name or None,
        "openrouter_guardrails": "managed by the OpenRouter workspace or API key",
        "boundary": "OpenRouter guardrails run after content reaches OpenRouter and before the model provider",
    }


def scan_text(text: str, *, source: str) -> str | None:
    module_name = os.environ.get(SCANNER_ENV, "").strip()
    if not module_name:
        return None
    scanner = _load_scanner(module_name)
    try:
        result = scanner(text, source=source)
    except Exception as exc:  # noqa: BLE001 - fail closed at extension boundary
        raise SafetyScannerError(
            f"configured local safety scanner failed for {source}: {type(exc).__name__}"
        ) from exc
    if result is not None and (not isinstance(result, str) or not result.strip()):
        raise SafetyScannerError(
            "configured local safety scanner must return None or a non-empty finding string"
        )
    if isinstance(result, str):
        finding = result.strip()
        if len(finding) > 200 or any(character in finding for character in "\r\n"):
            raise SafetyScannerError(
                "configured local safety scanner finding must be one line of at most 200 characters"
            )
        return finding
    return None


@functools.lru_cache(maxsize=8)
def _load_scanner(module_name: str) -> Scanner:
    try:
        module: ModuleType = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - fail closed at extension boundary
        raise SafetyScannerError(
            f"could not load configured local safety scanner {module_name!r}: {type(exc).__name__}"
        ) from exc
    scanner = getattr(module, "scan_text", None)
    if not callable(scanner):
        raise SafetyScannerError(
            f"configured local safety scanner {module_name!r} has no callable scan_text"
        )
    return scanner
