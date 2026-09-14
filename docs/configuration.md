# Codex configuration

Install the package into a stable Python 3.11+ environment, then add the STDIO
server to the user-level `~/.codex/config.toml`. Use absolute paths.

```toml
[mcp_servers.openrouter_delegator]
command = "/absolute/path/to/python"
args = ["-m", "codex_openrouter_delegator"]
required = true
startup_timeout_sec = 20
tool_timeout_sec = 360
default_tools_approval_mode = "writes"
enabled_tools = [
  "list_profiles",
  "delegate_task",
  "start_task",
  "get_task_status",
  "get_task_result",
  "send_followup",
  "cancel_task",
  "prepare_artifact",
  "preview_artifact",
  "commit_artifact",
  "discard_artifact",
  "list_artifact_jobs",
]

[mcp_servers.openrouter_delegator.env]
OPENROUTER_ARTIFACT_ROOT_MODE = "cwd"

[mcp_servers.openrouter_delegator.tools.commit_artifact]
approval_mode = "prompt"
output_token_limit = 4000

[mcp_servers.openrouter_delegator.tools.preview_artifact]
output_token_limit = 8000

[mcp_servers.openrouter_delegator.tools.get_task_result]
output_token_limit = 16000
```

CWD artifact mode locks the server to the Codex task's startup working
directory and refuses a filesystem root or the user home directory. Use an
explicit `OPENROUTER_ARTIFACT_ROOT` instead when the MCP process does not start
in the project directory.

Restart ChatGPT desktop or begin a new CLI/IDE session, then use `/mcp` or
`codex mcp list` to verify the server.

## Windows

Create a generic credential with target `Codex/OpenRouter`, username
`openrouter`, and the dedicated key as its password. `scripts/openrouter_credential.ps1`
can set, test, rotate, or remove it from an ordinary PowerShell window.

Use the absolute Python executable from the virtual environment:

```toml
command = "C:/Users/<user>/.local/share/codex-openrouter-mcp/.venv/Scripts/python.exe"
```

## macOS

Create a Keychain application-password item with service `Codex/OpenRouter` and
account `openrouter`. The server uses `/usr/bin/security` to retrieve it.

Use the virtual environment interpreter:

```toml
command = "/Users/<user>/.local/share/codex-openrouter-mcp/.venv/bin/python"
```

## Linux

Install `secret-tool` (usually from `libsecret-tools`) and store the key:

```bash
secret-tool store --label='Codex OpenRouter' service 'Codex/OpenRouter' account openrouter
```

Use:

```toml
command = "/home/<user>/.local/share/codex-openrouter-mcp/.venv/bin/python"
```

For a headless host without Secret Service, inject `OPENROUTER_API_KEY` only
into the MCP process through a protected service environment or secret manager.
