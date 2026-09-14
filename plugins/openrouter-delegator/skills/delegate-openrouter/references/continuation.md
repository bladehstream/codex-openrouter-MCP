# Continuation guidance

Synchronous `delegate_task` and `review_files` results declare
`followup_supported: false`. Their `delegation_id` values are for audit
correlation and must not be passed to `send_followup`.

When continuation may be useful:

1. Use `start_task` for inline context or `start_file_review` for selected files.
2. Retain the returned `job_id`.
3. Monitor it with `get_task_status` and retrieve it with `get_task_result`.
4. Pass that `job_id` to `send_followup` with a focused instruction.

`start_file_review` retains the exact hashed file snapshot and full conversation
in MCP process memory. Do not paste or resend the files. Later filesystem
changes do not alter the retained review. If follow-up context exceeds the
server budget or the MCP process restarts, start a new review.

Returned reasoning, finalization, provider, usage, and version metadata are
audit signals. Use the answer only after normal local verification.
