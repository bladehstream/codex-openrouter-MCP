# Codex OpenRouter MCP

A local, security-focused STDIO MCP server that lets a Sol or Astra Codex parent
delegate bounded work to explicitly approved OpenRouter model/provider routes.

Current profiles:

| Profile | Model | Provider order |
| --- | --- | --- |
| `deepseek_high` | `deepseek/deepseek-v4.1-flash` | Fireworks, Relace, Novita, SiliconFlow |
| `glm_mechanical` | `~z-ai/glm-flash-latest` | Relace, Wafer |

Every request enforces Zero Data Retention, denies provider data collection,
and prevents routing outside the configured provider list.

## Capabilities

- synchronous delegation;
- selected-file review for up to 100 UTF-8 source and text files, limited to
  500 KB each and 750 KB combined;
- follow-up-capable asynchronous file review with an in-memory hashed snapshot;
- compatibility with externally configured OpenRouter workspace/API-key
  guardrails, with an optional user-supplied local pre-transmission scanner;
- versioned, weighted model/provider profiles with a validated external JSON
  override and configuration hash;
- in-memory asynchronous jobs, status, follow-up, result, and cancellation;
- selected-file artifact preparation;
- in-memory artifact preview with SHA-256 manifests;
- approval-oriented atomic new-file creation under `artifacts/openrouter/`;
- Windows Credential Manager, macOS Keychain, and Linux Secret Service support;
- no runtime Python dependencies.

The artifact boundary does not provide external models with shell access,
arbitrary file reads, source-tree writes, or existing-file replacement.

OpenRouter guardrails are not provisioned or verified by this MCP. Without an
optional local scanner, selected content reaches OpenRouter before any assigned
OpenRouter guardrail evaluates it.

## Install for development

```bash
uv sync --python 3.11
```

Run the server:

```bash
uv run codex-openrouter-mcp
```

See [Codex configuration](docs/configuration.md) for setup and the
[security policy](SECURITY.md) for the current trust boundary.
See [delegation and continuation](docs/delegation.md) for synchronous versus
asynchronous IDs, file-review follow-ups, reasoning budgets, and finalization.
See [routing configuration](docs/routing-config.md) to change models, providers,
weights, reasoning policy, or profile instructions without editing Python.

For skill-guided installation through the repository's Git marketplace, see
[plugin installation](docs/plugin.md). The bundled `delegate-openrouter` skill
teaches Codex how to route work, preserve the parent model's coordination role,
verify delegate output, and use the approval-gated artifact workflow.

## Tests

```bash
uv run python -m unittest discover -s tests -p "test_*.py" -v
```

Paid live tests are intentionally excluded from CI:

```bash
uv run python tests/live_acceptance.py
```

## Status

Alpha. Inline delegation, bounded selected-file review, and inert text artifacts
are implemented and tested. Near-native repository exploration, patching,
worktrees, and test execution are planned as separately gated capabilities.
