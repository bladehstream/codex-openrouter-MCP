# Security boundary

## General delegation

`delegate_task` and asynchronous job tools send only text explicitly supplied
by the Sol/Astra parent. The external model has no repository, filesystem,
shell, browser, plugin, or nested-delegation tools.

Inline tasks accept up to 200,000 characters. `review_files` is the preferred
path for larger reviews: it reads only 1-20 explicitly named UTF-8 text or
source files under the locked workspace root, up to 500 KB per file and 750 KB
combined. It applies the same traversal, link, sensitive-name, and likely-secret
checks before transmitting content, and returns the reviewed paths, byte counts,
and SHA-256 hashes with the model result. It does not grant the model general
filesystem access.

## Artifact delegation

`prepare_artifact` can read selected UTF-8 `.md`, `.txt`, `.json`, `.csv`,
`.yaml`, and `.yml` files under the locked workspace root. Input contents are
marked as untrusted source material. The model must return one JSON artifact
object with exactly the requested filenames.
Artifact generation uses Chat Completions JSON-object mode with deterministic
sampling. General delegation continues to use the Responses API.
If the first artifact response contains no unique valid artifact object, the
server permits one format-repair request. The invalid response is discarded;
the repair must pass the original path, format, content, size, secret, and hash
checks. A second invalid response fails closed without writing files.

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
