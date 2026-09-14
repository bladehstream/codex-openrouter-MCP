# Weighted model and provider configuration

The MCP loads `codex_openrouter_delegator/default_routes.json` by default. A
user-managed JSON file can replace the complete profile set without changing
Python or rebuilding the plugin.

## Current bundled priorities

| Profile | Provider | Weight | Effective order |
| --- | --- | ---: | ---: |
| `deepseek_high` | Fireworks | 100 | 1 |
| `deepseek_high` | Relace | 90 | 2 |
| `deepseek_high` | Novita (NovitaAI) | 60 | 3 |
| `deepseek_high` | SiliconFlow | 50 | 4 |
| `glm_mechanical` | Relace | 100 | 1 |
| `glm_mechanical` | Wafer | 50 | 2 |

Higher weights are tried first. Equal weights preserve their order in the JSON
file. Weights range from 0 to 1000 and are preference scores, not percentages or
traffic shares. Because providers live inside a profile, a provider can have a
different weight for each model/profile combination.

The router sends the effective order in both OpenRouter's `provider.only` and
`provider.order` fields, keeps `allow_fallbacks` closed to that list, requires
parameter compatibility, enforces ZDR, and denies provider data collection.

OpenRouter combines this request allowlist with provider restrictions assigned
to the API key or workspace guardrail. A provider must be allowed by both. If a
locally configured provider is absent from the OpenRouter guardrail, OpenRouter
rejects that endpoint before inference; the MCP does not and cannot override the
account policy. Add `Novita` and `SiliconFlow` to the dedicated key's provider
allowlist before expecting the new last-resort routes to run.

After changing the guardrail, verify both endpoints independently:

```powershell
uv run python tests/live_acceptance.py --case last-resorts
```

This paid opt-in case pins one request to each provider. It is not part of the
default live suite because an intentionally narrower account guardrail should
not make unrelated acceptance checks fail.

## Create an external configuration

After installing v0.4.0, print the bundled configuration from PowerShell:

```powershell
$routeFile = Join-Path $env:LOCALAPPDATA 'codex-openrouter-routes.json'
codex-openrouter-routes --show-default | Set-Content -Encoding utf8 $routeFile
codex-openrouter-routes $routeFile
```

Edit the file, validate it again, then make it available to the plugin:

```powershell
[Environment]::SetEnvironmentVariable(
    'OPENROUTER_ROUTES_FILE',
    $routeFile,
    'User'
)
```

Close and reopen Codex after changing the file or environment variable. A route
file is loaded once at MCP process startup; there is deliberately no mutable
hot-reload tool.

Remove the user environment variable to return to the bundled defaults:

```powershell
[Environment]::SetEnvironmentVariable('OPENROUTER_ROUTES_FILE', $null, 'User')
```

## Schema

```json
{
  "version": 1,
  "profiles": {
    "review_profile": {
      "role": "high-level",
      "model": "vendor/model",
      "resolved_model_pattern": "^vendor/model(?:-[0-9.]+)?$",
      "instructions": "Return a concise evidence-based review.",
      "reasoning": {
        "effort": "low",
        "exclude": true
      },
      "providers": [
        {"slug": "preferred", "display": "Preferred", "weight": 100},
        {"slug": "backup", "display": "Backup", "weight": 40}
      ]
    }
  }
}
```

`resolved_model_pattern` is optional. Omit it for a fixed model, in which case
the returned model must exactly match `model`. Use it for a latest-model alias
whose resolved slug can change within an explicitly approved family.

Provider `slug` is the value used in OpenRouter routing. Provider `display` must
match the name returned in OpenRouter routing metadata so the response audit can
reject an unexpected provider. Use OpenRouter's model endpoints catalogue to
confirm both values. OpenRouter currently reports the NovitaAI service as
display `Novita` with base slug `novita`, and SiliconFlow with base slug
`siliconflow`.

Configuration is limited to 1 MB, 16 profiles, and 8 providers per profile.
Unknown fields, duplicate JSON keys, duplicate provider slugs/displays, invalid
weights, malformed names, invalid model patterns, and unsupported configuration
versions fail closed. `list_profiles` reports whether the bundled or external
file is active, its path when external, its SHA-256 hash, and effective weighted
provider order.

OpenRouter references:

- [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)
- [Model endpoints catalogue](https://openrouter.ai/docs/api/api-reference/endpoints/list-endpoints)
- [ZDR endpoint catalogue](https://openrouter.ai/docs/api/api-reference/endpoints/list-endpoints-zdr)
