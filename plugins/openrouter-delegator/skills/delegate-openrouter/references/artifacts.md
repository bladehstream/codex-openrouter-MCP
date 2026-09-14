# Artifact workflow

Artifact tools provide a narrow, approval-oriented path for creating new inert text files. They do not grant general repository write access.

1. Select only the necessary allowed text inputs and explicit output paths.
2. Call `prepare_artifact` with the appropriate profile, bounded instructions, input paths, and outputs.
3. Call `preview_artifact` and inspect every path, content preview, content hash, and the manifest SHA-256.
4. Describe the proposed files to the user and obtain explicit approval to commit that exact manifest.
5. Call `commit_artifact` with the exact `job_id` and `expected_manifest_sha256` from the reviewed preview.
6. Verify the created files locally. Run relevant parsers, formatters, or tests when available.

Use `discard_artifact` when the proposal is rejected or obsolete. A changed proposal requires another preview and approval. Do not commit an artifact if its manifest, paths, or content no longer match what the user approved.

The server creates new files only under `artifacts/openrouter/`. It rejects existing-file replacement, unsupported formats, path traversal, unsafe links, excessive inputs, and oversized content. Treat rejection as a boundary, not an obstacle to bypass.
