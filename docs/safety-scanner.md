# Content guardrails and optional local scanning

## Default: OpenRouter guardrails

Configure guardrails in OpenRouter under **Settings > Privacy > Guardrails** and
assign the policy to the dedicated API key or its workspace. Relevant controls
include OpenRouter-maintained prompt-injection detection, sensitive-info
presets, and user-defined content filters. The MCP does not create, require, or
verify this configuration.

OpenRouter guardrails receive the request at OpenRouter and apply before the
request is forwarded to Fireworks, Relace, Wafer, or another approved provider.
They are therefore provider-side controls, not endpoint-local data-loss
prevention. The MCP cannot verify the guardrail configuration with an ordinary
inference key and reports it as externally managed.

OpenRouter currently documents built-in sensitive-info presets for email,
phone, SSN, credit-card, IP-address, person-name, and address data. Arbitrary API
keys and product-specific credentials require custom filters unless OpenRouter
adds a suitable maintained preset. Start new or changed regex guardrails in
`flag` mode against representative code before choosing `redact` or `block`.

## Optional: local scanner module

Local content scanning is disabled by default. This means content is not
secret-scanned on the endpoint unless a module is configured. To enforce policy before content
leaves the machine, install a Python module into the same uv tool environment
and set `OPENROUTER_SAFETY_SCANNER_MODULE` to its import name. The module must
export:

```python
def scan_text(text: str, *, source: str) -> str | None:
    """Return a short finding to block, or None to allow."""
```

The `source` value identifies the boundary, such as
`review-input:server/app.py`, `input:notes.md`, or
`generated-output:report.md`. Do not return matched secret text. Keep findings
short and non-sensitive.

A configured scanner applies to inline delegation requests, selected review
inputs, artifact inputs, and generated artifact outputs. The MCP fails closed
when the module cannot be loaded, raises an exception, or returns anything
other than `None` or a short, single-line finding string.

For a scanner distributed as a Python package at a local path:

```powershell
uv tool install --force --python 3.11 --with 'C:\path\to\scanner-package' .
[Environment]::SetEnvironmentVariable(
    'OPENROUTER_SAFETY_SCANNER_MODULE',
    'company_codex_scanner',
    'User'
)
```

Close Codex before replacing the uv tool environment, then reopen Codex so the
MCP inherits the new user environment variable. Remove that variable to return
to the externally managed OpenRouter policy only; if no OpenRouter guardrail is
assigned, no content scanner is active.

OpenRouter references:

- [Guardrails overview](https://openrouter.ai/docs/guides/features/guardrails/overview)
- [Prompt-injection detection](https://openrouter.ai/docs/guides/features/guardrails/prompt-injection)
- [Sensitive-information guardrails](https://openrouter.ai/docs/guides/features/guardrails/sensitive-info)
