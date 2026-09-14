# Implementation plan

This plan turns the unchecked work in `TODO.md` into dependency-ordered releases
and independently verifiable work packages. It starts from v0.4.1. Target
versions express compatibility boundaries, not delivery dates.

The universal ChatGPT/Codex plugin directory remains deferred. Repository
visibility and directory submission are human-only governance actions under
`AGENTS.md`.

## Delivery principles

1. Expand authority one capability at a time: discover, read, propose, isolate,
   execute, approve, then integrate.
2. Keep the primary checkout, arbitrary shell execution, credentials, provider
   policy, and final acceptance outside the external model's authority.
3. Bind every material operation to immutable paths, revisions, hashes,
   manifests, policies, and approvals.
4. Put resource limits, lifecycle cleanup, error taxonomy, audit schema, and
   adversarial tests in place before adding write or execution capability.
5. Prefer explicit configuration and deterministic behavior over dynamic
   convenience. Recommendations may be automatic; policy changes are not.
6. Treat documentation, cross-platform tests, upgrade behavior, and failure
   recovery as part of each feature's definition of done.
7. Dogfood external delegation without outsourcing coordination: Sol or Astra
   owns architecture, authorization, verification, and release decisions.

## Roadmap overview

| Milestone | Target | Boundary added | Depends on | Gate |
| --- | --- | --- | --- | --- |
| M0 | v0.4.x | Public-alpha governance and release hygiene | Current baseline | Public operations are supportable |
| M1 | v0.5.0 | Bounded runtime, credentials, errors, audit foundation | M0 policy decisions | Existing capabilities cannot exhaust or silently outlive policy |
| M2 | v0.6.0 | Bounded repository discovery and reads | M1 | Repository snapshot is deterministic and read-only |
| M3 | v0.7.0 | Structured patch proposals without writes | M2 | Every proposal is hash-bound and inert |
| M4 | v0.8.0 | Patch application in isolated worktrees | M1, M3 | No primary-checkout writes are possible |
| M5 | v0.9.0 | Allowlisted build and test execution | M1, M4 | No arbitrary shell or unbounded execution |
| M6 | v0.10.0 | Approval-bound integration and rollback | M3-M5 | Primary integration requires a distinct immutable approval |
| M7 | v0.11.0 | Security-reviewed public beta | M1-M6 | Cross-platform adversarial suite and independent review pass |
| M8 | Later | Coding-agent UX, scale, and quality evaluation | M6-M7 | Useful near-native workflow without broader authority |
| Directory gate | Unscheduled | Universal directory submission | All deferred gates | Human decision only |

The critical path is:

```text
M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → human directory decision
```

Provider operations, packaging, and selected observability work run alongside
that path when their listed dependencies are satisfied.

## M0 — Public-alpha governance and release hygiene

Goal: make the public repository supportable without implying directory or
production readiness.

### Work packages

- **M0.1 — Security intake:** prepare private-vulnerability-reporting guidance;
  ask the owner to enable the GitHub feature; verify the public reporting path
  without submitting a real vulnerability.
- **M0.2 — History and CI hardening:** run Gitleaks or TruffleHog over all refs,
  triage synthetic fixtures, pin Actions to reviewed SHAs, and prepare owner-only
  branch-protection/Dependabot/CodeQL changes.
- **M0.3 — Release mechanics:** add `CHANGELOG.md`, immutable tag and checksum
  procedure, release checklist, recovery procedure, and stable public
  `HTTP-Referer` metadata.
- **M0.4 — Community boundary:** add support and compatibility policy,
  standalone privacy/data-flow notice, `CONTRIBUTING.md`, model/provider
  acceptance criteria, and contributor/CLA terms before accepting substantive
  contributions that might affect future dual licensing.
- **M0.5 — Documentation:** add VPS/headless Linux, desktop Linux, macOS,
  Windows, private/public marketplace, troubleshooting, and upgrade guides.

### Parallelism

M0.1-M0.5 can proceed independently. Repository-setting changes remain owner
actions; agents prepare and verify instructions only.

### Exit criteria

- Every unchecked P0 public-hygiene item is complete or linked to an explicit
  human-owned action.
- Full-history scanning is recorded with only reviewed false-positive ignores.
- CI action pins and the release checklist are reproducible.
- Public metadata, support scope, contributor terms, and security contact are
  unambiguous.
- Documentation link, package, plugin, and cross-platform unit tests pass.

## M1 — Runtime, credential, error, and audit foundation

Goal: bound the capabilities that already exist before retaining more data or
adding code execution.

### Work packages

- **M1.1 — Job manager:** replace the unbounded dictionary with a lifecycle
  component enforcing configurable queued, running, completed, and total job
  counts; per-job and aggregate retained-byte budgets; and deterministic
  admission errors.
- **M1.2 — Expiry and cleanup:** implement monotonic TTLs, terminal-job expiry,
  snapshot/history cleanup, eviction reasons, testable clock injection, and
  shutdown cleanup.
- **M1.3 — Cancellation:** introduce cancellation tokens through the job and
  HTTP layers; close in-flight requests where supported; otherwise expose a
  precise `cancel_requested_but_transport_running` state.
- **M1.4 — Error model:** define stable machine-readable error codes and sanitize
  authorization headers, bearer values, credential URLs, common key formats,
  provider payloads, and exception chains without hiding actionable metadata.
- **M1.5 — Headless credentials:** add a pluggable credential-provider protocol
  and at least one permission-checked VPS backend, with process-only scoping and
  no secret values in CLI arguments, logs, or tool results.
- **M1.6 — Configuration trust:** check ownership and permissions for external
  route files and scanner packages, record their hashes, and require an explicit
  override for deliberately shared configurations.
- **M1.7 — Audit v2:** specify event schemas, redaction classes, retention and
  rotation, job/delegation correlation, and default metadata-only behavior. The
  retention/redaction policy must be machine-checkable before persistence.
- **M1.8 — Diagnostics:** add a bootstrap/check command for runtime/plugin
  versions, PATH, credentials, workspace root, guardrail expectation, route
  hash, resource limits, and known platform constraints.
- **M1.9 — Windows output:** make CLI, diagnostic, and live-test output
  explicitly UTF-8 and cover legacy Windows console encodings.

### Parallelism

M1.4-M1.6 and M1.9 are independent. M1.1 and M1.2 share the lifecycle model;
M1.3 builds on it. M1.7 defines correlation fields before M1.8 and later tools
emit them.

### Exit criteria

- Admission, memory, count, TTL, cleanup, and cancellation behavior is bounded
  and observable under concurrency.
- Credential and configuration backends fail closed with actionable redacted
  errors.
- Audit output cannot contain prompt, source, response, or credential content by
  default.
- Stress tests demonstrate stable retained memory at configured limits.
- Windows, Linux, and macOS suites pass; headless Linux credential behavior is
  exercised on a real or representative runner.

## M2 — Bounded repository discovery and reads

Goal: let delegates request useful repository context without granting general
filesystem or shell access.

### Work packages

- **M2.1 — Repository snapshot:** define a snapshot ID bound to root, Git
  directory, revision, dirty-state metadata, ignore policy, and configuration
  hash.
- **M2.2 — Shared path policy:** centralize canonicalization and enforcement for
  traversal, drives, UNC/device paths, ADS, reserved names, case folding,
  symlinks, junctions, reparse points, hard links, mounts, and nested roots.
- **M2.3 — Inventory tool:** return bounded path/type/size/hash metadata with
  explicit truncation and no content.
- **M2.4 — File selection tool:** support structured extension/path filters,
  count and byte limits, deterministic ordering, and explicit include/exclude
  rules without escape-capable raw globs.
- **M2.5 — Text search tool:** implement literal and constrained-regex search
  with bounded matches, line excerpts, encoding rules, and no shell invocation.
- **M2.6 — Read tool:** return explicitly selected UTF-8 content with path,
  bytes, SHA-256, line ranges, truncation metadata, and snapshot binding.
- **M2.7 — Repository variants:** define and test submodules, sparse checkouts,
  ignored/generated files, existing worktrees, nested repositories, and dirty
  files.
- **M2.8 — TOCTOU protection:** revalidate identity and hash after read; reject
  or clearly version files changed between selection and transmission.

### Parallelism

M2.1-M2.2 define shared contracts first. M2.3-M2.6 can then run in parallel.
M2.7-M2.8 exercise all tools and close the milestone.

### Exit criteria

- Every result is bound to a locked root and repository snapshot.
- No search or read path invokes a shell or escapes the shared path policy.
- Every content-bearing result supplies exact hashes and truncation state.
- Cross-platform path, link, mount, encoding, and mutation-race tests pass.

## M3 — Structured patch proposals without writes

Goal: allow external models to propose code changes while the MCP remains
read-only.

### Work packages

- **M3.1 — Proposal schema:** define versioned files, operations, base hashes,
  hunks, modes, limits, provenance, route metadata, and expected outputs.
- **M3.2 — Parser:** parse unified diffs in-process without invoking `git apply`,
  a shell, or an interpreter.
- **M3.3 — Policy validation:** reject absolute/traversing paths, binary patches,
  unsupported modes, unsafe renames, unexpected files, oversized changes,
  overlapping hunks, and base mismatches.
- **M3.4 — Preview and manifest:** render a bounded normalized diff and immutable
  proposal hash without writing files.
- **M3.5 — Revision:** support focused follow-ups while retaining original
  snapshot, previous proposal, reviewer provenance, and invalidation history.
- **M3.6 — Review tools:** expose create/status/result/preview/discard operations
  with accurate read-only annotations and no ambiguous continuation IDs.

### Exit criteria

- Valid proposals reproduce deterministic normalized diffs and hashes.
- Every rejected class has a stable error code and adversarial fixture.
- A proposal cannot refer to content outside its exact M2 snapshot.
- Filesystem write monitoring proves proposal workflows are inert.

## M4 — Isolated patch application

Goal: apply an approved proposal only inside a verified disposable workspace.

### Work packages

- **M4.1 — Isolation abstraction:** define Git-worktree and non-Git staging
  interfaces; implement Git worktrees first.
- **M4.2 — Target verification:** resolve repository, Git directory, base
  revision, primary checkout, sibling worktrees, destination, and ownership
  before mutation.
- **M4.3 — Apply engine:** apply only an immutable M3 proposal with matching base
  hashes; no arbitrary patch file or shell command.
- **M4.4 — Conflict handling:** detect changed bases, rejected hunks, mode
  conflicts, and unexpected generated/untracked files.
- **M4.5 — Result manifest:** record resulting tree/diff, file hashes, untracked
  files, proposal hash, and audit correlation.
- **M4.6 — Lifecycle:** enforce worktree count, disk budget, TTL, recoverable
  cleanup, and crash-recovery inventory.

### Exit criteria

- Primary and unrelated worktrees remain byte-for-byte untouched in positive,
  negative, cancellation, timeout, and crash tests.
- Only an approved hash-bound proposal can mutate the isolated workspace.
- Conflicts fail closed; cleanup is bounded and recoverable.

## M5 — Allowlisted build and test execution

Goal: run useful verification in isolation without introducing arbitrary shell
authority.

### Work packages

- **M5.1 — Command policy schema:** define project-owned templates with exact
  executable identity, ordered argument matchers, permitted working directory,
  environment, network, resources, and output policy.
- **M5.2 — Invocation validator:** accept argv arrays only; reject shell strings,
  metacharacter interpretation, substitutions, response files, path escapes,
  and interpreter trampoline patterns unless explicitly modeled.
- **M5.3 — Process supervisor:** enforce timeout, process count, CPU, memory,
  output size, cancellation, and descendant cleanup per platform.
- **M5.4 — Environment policy:** construct a minimal allowlisted environment,
  strip secrets, and record names/policy rather than values.
- **M5.5 — Results:** classify pass, test failure, infrastructure failure,
  timeout, cancellation, policy rejection, and resource termination; retain
  bounded output with truncation hashes.
- **M5.6 — Progress:** stream bounded progress while producing one deterministic
  final result and audit record.

### Exit criteria

- No unmodeled executable, argument, directory, environment variable, network
  access, or child process succeeds.
- Tests run in the M4 isolated worktree by default.
- Failure classes, limits, output redaction, and cleanup pass adversarial and
  cross-platform suites.

## M6 — Approval-bound integration and rollback

Goal: move verified changes into the primary checkout only after a distinct,
immutable human approval.

### Work packages

- **M6.1 — Integration manifest:** combine proposal, isolated result, commands,
  tests, file hashes, route/model/provider, and audit IDs into one immutable
  approval target.
- **M6.2 — Preview:** present exact diff, test evidence, dirty-checkout state,
  conflicts, rollback scope, and manifest hash.
- **M6.3 — Approval boundary:** require a separate prompt-mode tool call carrying
  the exact manifest hash; approvals cannot be inferred from earlier review or
  patch authorization.
- **M6.4 — Invalidation:** reject reuse after any file, revision, route, model,
  provider, command, policy, test result, or primary-checkout change.
- **M6.5 — Integration:** preserve unrelated dirty changes and apply only the
  approved delta without `reset --hard`, checkout-based discards, or hidden
  commits.
- **M6.6 — Rollback:** provide a recoverable rollback artifact and explicitly
  document cases that cannot be automatically reversed.
- **M6.7 — External mutations:** keep push, pull request, deployment, release,
  publication, and repository governance outside this capability; each requires
  distinct authorization and some remain permanently human-only.

### Exit criteria

- Every invalidation dimension has a positive and negative test.
- Dirty primary worktrees retain unrelated content.
- Integration is impossible without a current exact approval hash.
- Rollback behavior is demonstrated and limitations are explicit.

## M7 — Adversarial suite and independent security review

Goal: establish evidence for a public beta after the full permission ladder is
implemented.

### Work packages

- **M7.1 — Threat model:** publish assets, principals, boundaries, entry points,
  attacker capabilities, abuse cases, mitigations, and accepted residual risk.
- **M7.2 — Prompt injection:** exercise hostile instructions in source, docs,
  issues, logs, test output, patches, repository instructions, and delegate
  responses.
- **M7.3 — Boundary attacks:** request secrets, broader roots, provider changes,
  approval bypass, shell execution, objective replacement, and governance
  actions.
- **M7.4 — Fuzzing:** JSON-RPC, configuration, path normalization, archives,
  patch parsing, argument matching, manifests, and state transitions.
- **M7.5 — Stress and races:** concurrency, budgets, cancellation, expiry,
  cleanup, TOCTOU, disk exhaustion, output flooding, and restart recovery.
- **M7.6 — Platform suites:** privileged Windows filesystem cases and Linux/macOS
  link, mount, permission, process, and socket cases.
- **M7.7 — Provider failures:** outages, malformed/partial responses,
  reasoning-only output, finalization failure, bad metadata, guardrail rejection,
  and changing endpoint capabilities.
- **M7.8 — Independent review:** provide the threat model, raw tests, code, and
  minimal prior conclusions to an independent reviewer; triage and close
  material findings before beta.

### Exit criteria

- Supported-host adversarial and stress suites pass from clean installations.
- The independent report and disposition are public.
- Primary-tree writes remain disabled until the review gate is explicitly met.

## Parallel workstream A — Model and provider operations

This stream may begin after M1.4 error sanitization and can run beside M2-M6.

- Add read-only diagnostics against OpenRouter model, endpoint, ZDR, parameter,
  deprecation, context, price, latency, throughput, uptime, and guardrail data.
- Add preflight that predicts why configured endpoints would be excluded before
  a paid request.
- Add recommendations that combine live metrics and user weights but never
  alter route policy automatically.
- Add per-job cost estimates and spending ceilings below the API-key budget.
- Define route schema v2 migration before layering system, user, host, project,
  and task overrides with deterministic precedence and layer hashes.
- Detect non-empty but incomplete Responses results and either perform one
  bounded continuation or expose a typed partial-result state with truncation
  metadata.
- Verify whether Responses requests preserve weighted provider order in actual
  attempt metadata; do not claim ordering guarantees beyond observed and
  documented OpenRouter behavior.
- Keep restart-only loading until atomic reload and active-job semantics are
  specified and tested.
- Keep model/provider additions explicit, reviewed, and user-approved.

Exit criteria: diagnostics are read-only and redacted; recommendations are
advisory; route changes always produce a reviewable file/hash change.

## Parallel workstream B — Observability and lifecycle

Audit v2 begins in M1 and is extended at every later milestone.

- Correlate job, delegation, route hash, snapshot, proposal, worktree, command,
  approval, integration, finalization, provider attempt, and output manifest.
- Keep prompt, source, response, and secrets out of default audit events.
- Add queue, retained-byte, latency, token, cost, provider, cancellation, expiry,
  command, and cleanup metrics.
- Add rotation and retention controls before persistence.
- Consider encrypted resumable state only after key management, deletion, expiry,
  and recovery are defined; remain in-memory by default.

## Parallel workstream C — Packaging and compatibility

This stream starts in M0 and follows each release.

- Test built wheels and fresh uv tool installs on Windows, macOS, and Linux.
- Test upgrade, downgrade, rollback, PATH pickup, plugin cache-busting, and
  Windows running-process locks.
- Maintain a compatibility matrix for Codex, Python, operating systems, plugin
  manifests, route schemas, and OpenRouter APIs.
- Publish to PyPI only after trusted publishing, ownership protection, signed
  releases, and recovery procedures exist.
- Evaluate portable Agent Plugins packaging after the local compatibility
  manifest and permission model stabilize.
- Keep installation and troubleshooting guides executable and tested.

## M8 — Coding-agent experience and scale

Begin only after M6 and mature alongside M7.

- Add path-and-line citations to reviews, proposals, test failures, and diffs.
- Add multiple bounded reviewer roles without nested uncontrolled delegation.
- Add concurrent delegates under aggregate cost, job, and memory budgets.
- Add reusable task presets separate from security and route policy.
- Add concise progress, recovery guidance, and resumable user workflows.
- Evaluate external profiles against native Luna, Sol, and Astra task classes for
  correctness, cost, latency, and coordinator effort.

## Work-package execution protocol

Every package above follows the same evidence loop:

1. State the boundary change and update the threat-model delta.
2. Write a short architecture decision record when the change creates a durable
   interface or security invariant.
3. Define schemas, error codes, limits, and cleanup before implementation.
4. Add positive, negative, failure, race, and platform-appropriate tests.
5. Implement the smallest independently useful capability.
6. Dogfood `glm_mechanical` for bounded mechanical checks and `deepseek_high`
   for independent design/security review when the active route is healthy.
7. Have Sol or Astra reconcile the review and independently run local tests.
8. Update docs, TODO links, version metadata, plugin cache-bust, and changelog.
9. Build and inspect the wheel/plugin package.
10. Run targeted live acceptance only where behavior crosses OpenRouter.

External delegates never approve their own work, expand permissions, change
provider policy, integrate into the primary checkout, push, release, or perform
repository governance.

## Planning evidence and dogfooding

The initial dependency review was delegated through `start_file_review` to
`deepseek_high` using 34,974 bytes across `TODO.md`, `AGENTS.md`, `README.md`,
`SECURITY.md`, and the security, delegation, and routing references. Fireworks
completed the job with ZDR and provider data collection denied. The review
supported the M1-M7 critical path and the separation of parallel workstreams.

The coordinating plan deliberately changed two recommendations: audit schema and
retention moved into M1 instead of following write capability, and isolated
patching, command execution, and primary integration remain separate releases.

The dogfood run also exposed two roadmap inputs:

- Windows console output must be explicitly UTF-8; the first completed result
  could not be printed through the legacy code page.
- A finalization response may contain text while still ending at its output
  budget. Partial-result detection must inspect response status and incomplete
  metadata rather than treating any non-empty text as complete.

A second independent critique was attempted but both currently guardrail-allowed
DeepSeek providers returned 429. It was not retried and no provider policy was
expanded.

## Planning and tracking structure

Use one issue or goal per numbered work package. Each must record:

- owner and reviewer;
- dependencies and blocked human actions;
- risk level and trust-boundary change;
- schema/config migrations;
- tests and platforms required;
- documentation and audit changes;
- rollback/cleanup behavior;
- release target and exit evidence.

Do not start a downstream milestone merely because implementation exists. Its
upstream exit criteria and security evidence must be complete.

## TODO coverage map

| TODO section | Planned delivery |
| --- | --- |
| Public repository hygiene | M0 |
| Current operational blockers | M0-M1 |
| Repository discovery and reads | M2 |
| Patch proposals without writes | M3 |
| Isolated patch application | M4 |
| Build and test execution | M5 |
| Approval, merge, and rollback | M6 |
| Adversarial tests and security review | M1-M7, final gate in M7 |
| Model and provider operations | Parallel workstream A |
| Observability and lifecycle | M1 plus parallel workstream B |
| Packaging and compatibility | M0 plus parallel workstream C |
| Coding-agent experience | M8 |
| Universal directory submission | Deferred human decision after M7/M8 gates |

## Directory-readiness gate

Directory submission remains blocked until all of the following are true:

- M1-M7 exit criteria are satisfied on supported platforms.
- Read, patch, isolated-write, test, approval, integration, rollback, resource,
  credential, audit, and cleanup boundaries have independent evidence.
- The threat model and independent security review are public and material
  findings are resolved.
- Licensing, privacy, support, contribution, release, and vulnerability policies
  are complete.
- Representative external users have exercised the public Git marketplace
  alpha and their findings have been addressed.
- Then-current OpenAI submission and MCP review requirements are re-checked.
- The repository owner explicitly decides to submit; agents cannot perform that
  governance action.
