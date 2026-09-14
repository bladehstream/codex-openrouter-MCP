# Delegation, IDs, reasoning, and continuation

## Synchronous calls

`delegate_task` and `review_files` return a `delegation_id`. This identifier is
for audit correlation only; it is not stored in the in-memory job registry and
cannot be passed to `send_followup`. Both results include
`followup_supported: false` and a continuation hint.

Use synchronous calls when one response is sufficient.

## Asynchronous calls

`start_task` and `start_file_review` return a `job_id`. Use that value with:

- `get_task_status` while work is pending;
- `get_task_result` after completion;
- `send_followup` for a focused continuation;
- `cancel_task` when the result is no longer needed.

`start_file_review` reads and validates the selected files once, retains their
full content plus path/byte/SHA-256 manifest in process memory, and reuses that
exact snapshot for follow-ups. Later file changes do not silently alter the
review context. The server resends the full retained conversation because every
OpenRouter request uses `store: false`; it does not rely on provider-native
stored continuation.

Completed answers and follow-up instructions are retained without the former
12,000-character truncation. The reconstructed context has a 900,000-character
ceiling. Jobs and their retained content disappear when the MCP process exits.

## Reasoning and final answers

For `deepseek_high`, the server requests low reasoning effort and excludes
reasoning text from the returned payload. `glm_mechanical` requests no
reasoning. Reasoning tokens still count as output tokens when the upstream model
uses them.

Response parsing prefers the top-level `output_text`. Otherwise it accepts only
`output_text` blocks inside assistant `message` items; reasoning, analysis, and
summary items are ignored.

If a non-artifact request returns no assistant answer, the server performs one
automatic finalization call with reasoning disabled and a maximum of 4,000
output tokens or the original smaller limit. The result reports
`finalization_attempted`, `attempt_count`, aggregate token usage, and reported
reasoning tokens. If finalization still produces no assistant text, the task
fails instead of returning scratch reasoning as an answer.

See OpenRouter's [reasoning-token guidance](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
and [Responses API schema](https://openrouter.ai/docs/api/api-reference/responses/create-responses)
for the upstream token and item semantics.

## Version and guardrail status

`list_profiles` reports:

- the running MCP server version;
- the plugin base version supplied by the installed plugin;
- whether those versions match;
- optional local-scanner status;
- an expected OpenRouter guardrail label/ID when configured.
- the active route source and SHA-256 configuration hash.

An expected guardrail is reported as `configured_unverified`. The ordinary
inference credential cannot prove the external assignment, so the MCP never
reports it as verified.
