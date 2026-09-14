# Codex plugin and delegation skill

The repository includes a Git marketplace under `.agents/plugins` containing the `openrouter-delegator` plugin. The plugin bundles the `delegate-openrouter` skill and starts the existing local MCP package through the `codex-openrouter-mcp` console command.

## Runtime prerequisite

Install the MCP package so `codex-openrouter-mcp` is available on `PATH`. From a clone of this repository, `pipx` is the recommended cross-platform option:

```bash
pipx install .
```

Alternatively, install into a dedicated virtual environment and put its scripts/bin directory on `PATH`. On Windows, use the Python launcher or interpreter name configured on that machine. Keep the OpenRouter key in the operating-system credential store as described in [configuration.md](configuration.md); the plugin does not contain or install credentials.

Verify the command before installing the plugin:

```bash
codex-openrouter-mcp
```

The command waits for MCP input when healthy; end it with Ctrl+C.

## Add the Git marketplace

```bash
codex plugin marketplace add bladehstream/codex-openrouter-MCP --ref main
codex plugin add openrouter-delegator@codex-openrouter-mcp
```

For a private repository, Git authentication must already permit the clone. Restart Codex or ChatGPT desktop and begin a new task after installation.

If the MCP was previously configured directly under `[mcp_servers.openrouter_delegator]`, disable or remove that duplicate after confirming the plugin-backed server works. The plugin enables artifact mode against the task startup directory and keeps `commit_artifact` approval-gated.

## Upgrade

```bash
codex plugin marketplace upgrade codex-openrouter-mcp
codex plugin add openrouter-delegator@codex-openrouter-mcp
```

Start a new task so updated skill instructions and MCP metadata are loaded.
