"""Cross-platform retrieval of the Codex/OpenRouter credential."""

from __future__ import annotations

import ctypes
import os
import platform
import subprocess
from ctypes import wintypes


TARGET = "Codex/OpenRouter"
ACCOUNT = "openrouter"


def load_openrouter_key() -> str:
    environment_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if environment_key:
        return environment_key
    system = platform.system()
    if system == "Windows":
        return _windows_credential()
    if system == "Darwin":
        command = [
            "/usr/bin/security",
            "find-generic-password",
            "-s",
            TARGET,
            "-a",
            ACCOUNT,
            "-w",
        ]
    else:
        command = ["secret-tool", "lookup", "service", TARGET, "account", ACCOUNT]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=20, check=False
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"credential helper is not installed for {system}") from exc
    key = result.stdout.strip()
    if result.returncode != 0 or not key:
        raise RuntimeError(f"{TARGET} credential was not found for {system}")
    return key


def _windows_credential() -> str:
    class CREDENTIAL(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWrittenLow", wintypes.DWORD),
            ("LastWrittenHigh", wintypes.DWORD),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]

    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    credential_pointer = ctypes.POINTER(CREDENTIAL)()
    read = advapi.CredReadW
    read.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    read.restype = wintypes.BOOL
    free = advapi.CredFree
    free.argtypes = [ctypes.c_void_p]
    free.restype = None
    if not read(TARGET, 1, 0, ctypes.byref(credential_pointer)):
        raise RuntimeError(f"{TARGET} credential was not found (Windows error {ctypes.get_last_error()})")
    try:
        credential = credential_pointer.contents
        raw = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
        key = raw.decode("utf-16-le").strip()
        if not key:
            raise RuntimeError(f"{TARGET} credential is empty")
        return key
    finally:
        free(credential_pointer)
