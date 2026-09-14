# Security boundary

## General delegation

`delegate_task` and asynchronous job tools send only text explicitly supplied
by the Sol/Astra parent. The external model has no repository, filesystem,
shell, browser, plugin, or nested-delegation tools.

Inline tasks accept up to 200,000 characters. `review_files` is the preferred
path for larger reviews: it reads only 1-100 explicitly named UTF-8 text or
source files under the locked workspace root, up to 500 KB per file and 750 KB
combined. It applies traversal, link, sensitive-name, encoding, and optional
local-scanner checks before transmitting content, and returns the reviewed paths, byte counts,
SHA-256 hashes, and input-safety status with the model result. Content scanning
is handled by any externally assigned OpenRouter guardrails. The MCP does not
create or verify them. An optional user-supplied local scanner can run before
transmission. It does not grant the model general filesystem access.

## Artifact delegation

`prepare_artifact` can read selected UTF-8 `.md`, `.txt`, `.json`, `.csv`,
`.yaml`, and `.yml` files under the locked workspace root. Input contents are
marked as untrusted source material. The model must return one JSON artifact
object with exactly the requested filenames.
Artifact generation uses Chat Completions JSON-object mode with deterministic
sampling. General delegation continues to use the Responses API.
If the first artifact response contains no unique valid artifact object, the
server permits one format-repair request. The invalid response is discarded;
the repair must pass the original path, format, content, size, optional local
scanner, and hash checks. A second invalid response fails closed without writing
files.

## Content guardrails

Guardrails assigned to the dedicated API key or its OpenRouter workspace apply
to every delegation. OpenRouter receives the request before these filters run;
the filters can then flag, redact, or block content before provider forwarding.
The MCP does not attempt to mirror OpenRouter's maintained rules locally or
claim that a guardrail is configured.

Local pre-transmission filtering is disabled by default. Set
`OPENROUTER_SAFETY_SCANNER_MODULE` to a separately installed Python module when
an organization requires additional endpoint-local controls. The configured
module is applied to selected inputs and generated artifact content and fails
closed on load or execution errors. See
[content guardrails and optional local scanning](safety-scanner.md).

Preparation stores proposed bytes in memory. `preview_artifact` returns bounded
excerpts and hashes. `commit_artifact` requires the exact manifest hash and
atomically creates new files under `artifacts/openrouter/`; it cannot overwrite.

`discard_artifact` removes only an uncommitted in-memory proposal. It never
deletes a committed file.

## Planned near-native boundary

Coding and test execution must use separate tools and approvals:

1. bounded repository search and source reads;
2. patch proposals without writes;
3. isolated-worktree patch application;
4. allowlisted build and test command templates;
5. diff preview and expected-hash verification;
6. separately approved merge into the primary worktree.

Arbitrary shell strings and direct unrestricted source-tree writes are out of
scope for the current release.
