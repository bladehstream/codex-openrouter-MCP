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
  "review_files",
  "start_file_review",
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

# Optional: a separately installed local pre-transmission scanner module.
# OPENROUTER_SAFETY_SCANNER_MODULE = "company_codex_scanner"
# Optional: expected OpenRouter policy label or ID; this is reported but not verified.
# OPENROUTER_EXPECTED_GUARDRAIL = "engineering-review"
# Optional: validated external weighted model/provider profiles.
# OPENROUTER_ROUTES_FILE = "/absolute/path/to/routes.json"

[mcp_servers.openrouter_delegator.tools.commit_artifact]
approval_mode = "prompt"
output_token_limit = 4000

[mcp_servers.openrouter_delegator.tools.preview_artifact]
output_token_limit = 8000

[mcp_servers.openrouter_delegator.tools.get_task_result]
output_token_limit = 16000

[mcp_servers.openrouter_delegator.tools.review_files]
output_token_limit = 16000
```

CWD artifact mode locks artifact and selected-file review tools to the Codex
task's startup working directory and refuses a filesystem root or the user home
directory. Use an explicit `OPENROUTER_ARTIFACT_ROOT` instead when the MCP
process does not start in the project directory.

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

## Content guardrails

Assign the desired OpenRouter guardrail to the dedicated API key or workspace.
OpenRouter's maintained prompt-injection detector and sensitive-info controls
then apply after OpenRouter receives the request and before provider forwarding.
The MCP does not create or verify this external configuration. See
[content guardrails and optional local scanning](safety-scanner.md) for the
trust-boundary distinction and optional local scanner interface.

## Input limits

- `delegate_task` and `start_task`: 200,000 task characters.
- `review_files` and `start_file_review`: 1-100 unique files, 500 KB per file,
  750 KB combined.
- `prepare_artifact`: at most 20 input files and 10 output files.
- Generated artifact output: 1 MB per file and 5 MB combined.

`review_files` accepts UTF-8 text plus common source formats including Python,
JavaScript/TypeScript, Java, C/C++, C#, Go, Rust, Kotlin, Swift, Ruby, PHP,
Scala, shell, PowerShell, SQL, HTML/CSS, Vue, Svelte, XML, GraphQL, Protocol
Buffers, notebooks, INI, CFG, CONF, Markdown, JSON, YAML, TOML, CSV, and plain
text. Binary or invalid UTF-8 input is rejected. Rejection messages identify
the offending relative path.

## Models, providers, and weights

The server loads a validated bundled route configuration by default. Set
`OPENROUTER_ROUTES_FILE` to use an external versioned JSON file instead. This
can change profile models, instructions, reasoning policy, resolved-model
matching, provider allowlists, and priority weights without reinstalling the
package. Restart Codex after changing the file or environment variable.

Use `codex-openrouter-routes` to print or validate configuration. See
[routing configuration](routing-config.md) for the schema and workflow.
Remember that the effective provider set is the intersection of this file and
the OpenRouter API-key/workspace guardrail allowlist.
