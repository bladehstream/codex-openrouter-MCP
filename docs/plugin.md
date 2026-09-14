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

Verify `uv tool list` reports `codex-openrouter-mcp v0.3.0`, reopen Codex, and
start a new task so updated skill instructions and MCP metadata are loaded.
