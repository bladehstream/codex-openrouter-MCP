# Security policy

## Current trust boundary

The MCP server runs as the local user and can contact OpenRouter. General
delegation receives only text supplied in the tool call. External models have no
shell or filesystem tools.

Artifact jobs can read only explicitly named inert UTF-8 files beneath a root
locked at server startup. They stage output in memory and can create only new
top-level inert text files under `artifacts/openrouter/` after preview and an
exact manifest-hash check.

The implementation rejects traversal, absolute/UNC/device paths, Windows
alternate data streams and reserved names, symlinks, junctions, reparse points,
hard-linked inputs, sensitive filenames, likely credentials, existing outputs,
unsafe active links, duplicate JSON keys, CSV formula cells, and YAML custom
tags. File creation uses same-directory temporary files and atomic hard links so
an existing destination is never replaced.

MCP tool annotations are defense in depth, not the security boundary. Path,
content, size, format, and routing policies are enforced inside the server.

## Credentials

Use a dedicated, budget-limited OpenRouter key. Supported stores are Windows
Credential Manager (`Codex/OpenRouter`), macOS Keychain (service
`Codex/OpenRouter`, account `openrouter`), and Linux Secret Service. A process
environment key is supported only for protected headless deployments.

Never commit credentials, prompt logs, response content, or live-test audit
records. Ordinary CI does not receive an OpenRouter key and does not run paid
tests.

## Reporting

Keep this repository private during the alpha security review. Report suspected
path escapes, credential exposure, unapproved routing, overwrite behavior, or
command execution directly to the repository owner rather than opening a public
issue containing sensitive details.
