# Codex plugin and delegation skill

The repository includes a Git marketplace manifest under `.agents/plugins` and its `openrouter-delegator` package under the repository-level `plugins/` directory. Git marketplace source paths resolve from the installed repository root. The plugin bundles the `delegate-openrouter` skill and starts the existing local MCP package through the `codex-openrouter-mcp` console command.

## Runtime prerequisite

Install the MCP package so `codex-openrouter-mcp` is available on `PATH`. From a clone of this repository, use uv's isolated tool environment:

```bash
uv tool install --python 3.11 .
uv tool update-shell
```

Close and reopen the shell after the first `uv tool update-shell`. Alternatively, install into a dedicated virtual environment and put its scripts/bin directory on `PATH`. Keep the OpenRouter key in the operating-system credential store as described in [configuration.md](configuration.md); the plugin does not contain or install credentials.

Verify the command before installing the plugin:

```bash
codex-openrouter-mcp
```

The command waits for MCP input when healthy; end it with Ctrl+C.

On Windows, `Get-Command codex-openrouter-mcp` should resolve to uv's tool-bin
directory, normally under the user profile.

## Add the Git marketplace

```bash
codex plugin marketplace add bladehstream/codex-openrouter-MCP --ref main
codex plugin add openrouter-delegator@codex-openrouter-mcp
```

For a private repository, Git authentication must already permit the clone. Restart Codex or ChatGPT desktop and begin a new task after installation.

If the MCP was previously configured directly under `[mcp_servers.openrouter_delegator]`, disable or remove that duplicate after confirming the plugin-backed server works. The plugin enables artifact mode against the task startup directory and keeps `commit_artifact` approval-gated.

## Upgrade

Close Codex desktop and any Codex CLI sessions using this plugin before
replacing the uv tool environment. Windows locks the running MCP executable and
otherwise causes `uv tool install --force` to fail with `Access is denied`.

```bash
git pull --ff-only
uv tool install --force --python 3.11 .
codex plugin marketplace upgrade codex-openrouter-mcp
codex plugin add openrouter-delegator@codex-openrouter-mcp
```

Verify `uv tool list` reports `codex-openrouter-mcp v0.4.2`, reopen Codex, and
start a new task so updated skill instructions and MCP metadata are loaded.

Use `codex-openrouter-routes --show-default` and the workflow in
[routing configuration](routing-config.md) to manage weighted models and
providers without another package or plugin update.

## Recover from a broken MCP installation

The bundled MCP is intentionally optional. If Codex cannot start after an older
plugin release or partial uv upgrade, first edit the effective Codex
`config.toml` and temporarily disable the plugin:

```toml
[plugins."openrouter-delegator@codex-openrouter-mcp"]
enabled = false
```

`required` is not a valid setting in that plugin-enable table. It belongs to an
MCP server definition; v0.4.2 sets it to `false` in the bundled `.mcp.json`.

Close every Codex desktop and CLI process, then repair the uv environment from
the repository checkout:

```powershell
uv tool uninstall codex-openrouter-mcp
uv tool install --python 3.11 .
```

Before re-enabling the plugin, verify both imports and the MCP handshake:

```powershell
uv tool list
codex-openrouter-routes
'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' |
    codex-openrouter-mcp
```

The last command must return a JSON-RPC result containing `serverInfo`; it may
then exit when stdin closes. Upgrade/reinstall the marketplace plugin, set its
enable flag back to `true`, reopen Codex, and start a new task.
