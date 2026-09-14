# Routing guidance

## Profile selection

Choose `glm_mechanical` when the work has a clear procedure and correctness can be checked cheaply. Typical examples include producing a test matrix from supplied behavior, converting data or prose into a requested structure, drafting a small localized implementation from included context, and finding inconsistencies in a bounded excerpt.

Choose `deepseek_high` when the work benefits from competing hypotheses, cross-cutting tradeoffs, or a strong independent judgment. Typical examples include reviewing a supplied patch, designing an interface from stated constraints, reasoning about a subtle failure, threat-modeling a bounded feature, or proposing an implementation plan.

Treat `list_profiles` as authoritative for the active model and effective provider order. Profiles may come from a validated external configuration rather than the bundled defaults. Higher provider weights are tried first; equal weights preserve configuration-file order. A weight expresses preference for a model/provider combination, not a traffic percentage.

Keep the following with the coordinating Codex model:

- deciding the user's actual objective and resolving scope;
- reading the repository and selecting what context may leave the machine;
- tool permissions and user approvals;
- applying source changes and running local commands or tests;
- reconciling conflicting results and delivering the final answer.

## Decomposition

Split work along independently verifiable boundaries. Give each delegate only the context needed for its result. Prefer one coherent task over many tiny calls when the same context would be repeated; prefer separate calls when outputs can be evaluated independently or in parallel.

Ask for concise outputs with evidence, assumptions, risks, and a recommended next action where useful. For code proposals, request a patch or complete replacement fragment only when Codex has supplied the relevant source and can validate it locally.

## Capacity adjustment

Normal operation already favors the best-cost model for the task. Plan utilization is an adjustment, not the routing objective:

- Below 90% used: delegate whenever specialization, independent review, parallelism, or cost makes it useful.
- At or above 90% used: also send suitable Luna-class mechanical work to `glm_mechanical` to preserve coordinating capacity.
- Never send a task to the wrong profile merely to reduce ChatGPT usage.

If the coordinating model can no longer execute tool calls because a hard plan limit has been reached, this skill cannot keep the current turn running.
