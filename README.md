# Codex OpenRouter MCP

A local, security-focused STDIO MCP server that lets a Sol or Astra Codex parent
delegate bounded work to explicitly approved OpenRouter model/provider routes.

Current profiles:

| Profile | Model | Provider order |
| --- | --- | --- |
| `deepseek_high` | `deepseek/deepseek-v4.1-flash` | Fireworks, Relace |
| `glm_mechanical` | `~z-ai/glm-flash-latest` | Relace, Wafer |

Every request enforces Zero Data Retention, denies provider data collection,
and prevents routing outside the configured provider list.

## Capabilities

- synchronous delegation;
- in-memory asynchronous jobs, status, follow-up, result, and cancellation;
- selected-file artifact preparation;
- in-memory artifact preview with SHA-256 manifests;
- approval-oriented atomic new-file creation under `artifacts/openrouter/`;
- Windows Credential Manager, macOS Keychain, and Linux Secret Service support;
- no runtime Python dependencies.

The artifact boundary does not provide external models with shell access,
arbitrary file reads, source-tree writes, or existing-file replacement.

## Install for development

```bash
python3 -m venv .venv
python3 -m pip install -e .
```

Run the server:

```bash
codex-openrouter-mcp
```

See `docs/configuration.md` for Codex setup and `SECURITY.md` for the current
trust boundary.

For skill-guided installation through the repository's Git marketplace, see
`docs/plugin.md`. The bundled `delegate-openrouter` skill teaches Codex how to
route work, preserve the parent model's coordination role, verify delegate
output, and use the approval-gated artifact workflow.

## Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Paid live tests are intentionally excluded from CI:

```bash
python3 tests/live_acceptance.py
```

## Status

Alpha. Context-only delegation and inert text artifacts are implemented and
tested. Near-native repository exploration, patching, worktrees, and test
execution are planned as separately gated capabilities.
