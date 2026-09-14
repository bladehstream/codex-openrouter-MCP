# Troubleshooting

This runbook covers startup, installation, and file-access failures. The
OpenRouter delegator is an auxiliary capability: a failure must disable
delegation, not prevent Codex from starting.

## Codex cannot start a new task

A message containing `required MCP servers failed to initialize` means Codex
treated the delegator as a required startup dependency and could not complete
its MCP handshake.

### 1. Restore Codex access

Edit `%USERPROFILE%\.codex\config.toml` on Windows or
`~/.codex/config.toml` on macOS/Linux and temporarily disable the plugin:

```toml
[plugins."openrouter-delegator@codex-openrouter-mcp"]
enabled = false
```

Completely exit Codex desktop and any Codex CLI processes, then reopen Codex.

Do not add `required = false` to the `[plugins....]` table. Plugin enablement
and MCP startup policy are different settings. This repository's bundled
`.mcp.json` owns the MCP setting and must keep `required` set to `false`.

### 2. Identify the failing layer

From a normal shell, run:

```powershell
Get-Command codex-openrouter-mcp
uv tool list
codex-openrouter-routes
```

- A missing command means the uv tool bin directory is not on `PATH`, or the
  package has not been installed.
- `ModuleNotFoundError: No module named 'codex_openrouter_delegator'` means the
  uv tool environment is incomplete even if its launcher still exists.
- A routes error means the package starts but its routing configuration is
  invalid or inaccessible.

`codex mcp list` is useful for MCP servers configured directly in
`config.toml`, but it is not conclusive for a server bundled by a plugin. Use
`codex plugin list` to confirm the installed plugin version and location.

### 3. Repair an incomplete uv installation

On Windows, close Codex desktop and all Codex CLI sessions first. A running MCP
process can lock the tool's `Scripts` directory and cause `Access is denied`.
Then run these commands from the repository checkout:

```powershell
uv tool uninstall codex-openrouter-mcp
uv tool install --python 3.11 .
```

On macOS or Linux, use the same uv commands. If an executable is still in use,
stop the owning Codex process before reinstalling.

Do not hand-edit or delete files inside the Codex plugin cache. Upgrade through
the CLI so its manifest and bundled MCP definition remain consistent:

```powershell
codex plugin marketplace upgrade codex-openrouter-mcp
codex plugin add openrouter-delegator@codex-openrouter-mcp
```

### 4. Verify before re-enabling

First test the installed MCP launcher directly:

```powershell
'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' |
    codex-openrouter-mcp
```

It must return a JSON-RPC result containing `serverInfo`. Re-enable the plugin:

```toml
[plugins."openrouter-delegator@codex-openrouter-mcp"]
enabled = true
```

Restart Codex and test the complete startup path:

```powershell
codex exec --ephemeral --sandbox read-only --json "Reply with exactly MCP_STARTUP_OK. Do not call tools."
```

The output must include a started task, `MCP_STARTUP_OK`, and a completed turn.
This final test is important because a direct MCP handshake does not exercise
plugin discovery and Codex task initialization.

## File tools are unavailable but delegation works

Version 0.4.2 and later preserve the MCP handshake if artifact storage cannot
be initialized. `list_profiles` reports the file-access status, while
`review_files`, `start_file_review`, and artifact tools return an actionable
error.

The default plugin `cwd` mode intentionally refuses a filesystem root or a user
home directory. Start Codex inside the project directory. If you use the direct
MCP configuration from [configuration.md](configuration.md) instead of the
plugin, you can configure an explicit project-scoped path:

```toml
[mcp_servers.openrouter_delegator.env]
OPENROUTER_ARTIFACT_ROOT = "C:/absolute/path/to/project"
```

Use a platform-appropriate absolute path and restart Codex after changing it.
Do not add a direct MCP definition merely to override the plugin: that creates
two server definitions. Never broaden the artifact root to a home directory or
filesystem root merely to remove the error.

## Quick diagnosis

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Codex startup is blocked | Old bundled MCP has `required: true` | Disable the plugin, upgrade to v0.4.2+, verify, then re-enable |
| `Access is denied` during `uv tool install --force` | Codex is holding the Windows executable open | Fully exit desktop and CLI processes, then uninstall and install the tool |
| Launcher exists but raises `ModuleNotFoundError` | Partial uv tool environment or stale shim | Uninstall and reinstall the uv tool |
| Direct handshake succeeds but a new task fails | Plugin cache or Codex integration is stale | Upgrade/re-add the plugin and run the ephemeral Codex smoke test |
| Delegation works but file tools do not | Unsafe or unavailable artifact root | Start in the project or set a project-scoped explicit root |
| Server appears twice or behaves inconsistently | Both direct and plugin-backed MCP definitions are enabled | Keep one configuration route and disable the duplicate |
