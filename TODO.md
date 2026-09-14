# Public alpha roadmap

This repository is an unofficial public alpha. It is not affiliated with or
endorsed by OpenAI, OpenRouter, DeepSeek, Z.ai, or any listed inference
provider. The current release supports bounded delegation, selected-file
review, follow-up-capable in-memory jobs, weighted provider routing, and
approval-gated inert text artifacts. It is not yet a general external coding
agent runtime and is not ready for submission to the universal Codex plugin
directory.

Status as of v0.4.1:

- The repository owner has made the GitHub repository public. Repository
  visibility is permanently treated as a human-only action for automated agents;
  see `AGENTS.md`.
- 70 offline tests pass across the current suite.
- CI targets Windows, macOS, and Ubuntu with Python 3.11 and 3.12.
- The normal paid live suite passes.
- Novita and SiliconFlow are implemented as DeepSeek last-resort providers but
  remain blocked by the current dedicated key's OpenRouter guardrail until its
  provider allowlist is updated.
- The project is source-available under PolyForm Noncommercial 1.0.0. Commercial
  use is not granted by the public license.

## P0: public repository hygiene and immediate safety

- [x] Codify an absolute agent prohibition on changing repository visibility.
- [x] Add PolyForm Noncommercial 1.0.0 and publish matching SPDX package/plugin
  metadata.
- [x] Add the license's warranty/liability terms and a prominent public-alpha
  licensing summary.
- [ ] Add contributor terms or a CLA before accepting substantive external
  contributions if future commercial dual licensing is desired.
- [ ] Enable GitHub private vulnerability reporting and document the exact
  reporting path.
- [ ] Run Gitleaks or TruffleHog against the complete Git history before the
  first promoted public release; review synthetic-secret test fixtures and
  dismiss only confirmed false positives.
- [ ] Pin GitHub Actions to reviewed commit SHAs and enable automated updates for
  those pins.
- [ ] Enable branch protection, required cross-platform CI, Dependabot alerts,
  and CodeQL or an equivalent static-analysis workflow.
- [ ] Add `CHANGELOG.md`, signed or immutable version tags, release notes, and
  checksums for source and wheel artifacts.
- [ ] Replace the invalid placeholder `HTTP-Referer` with stable public project
  metadata and document what OpenRouter receives.
- [ ] Add a support policy covering alpha compatibility, response expectations,
  and unsupported environments.
- [ ] Add a standalone privacy/data-flow notice covering Codex, the local MCP,
  OpenRouter, guardrails, inference providers, audit metadata, retained jobs,
  and optional local scanners.
- [ ] Add a contributor guide and a policy for accepting new models/providers.

## P0: current operational blockers

- [ ] Add Novita and SiliconFlow to the OpenRouter guardrail assigned to the
  dedicated API key.
- [ ] Run `uv run python tests/live_acceptance.py --case last-resorts` and record
  successful provider identity, ZDR, and data-collection metadata for each.
- [ ] Add maximum queued, running, completed, and retained job counts.
- [ ] Add per-job and total retained-memory budgets for file snapshots and
  follow-up histories.
- [ ] Add job expiry/TTL, deterministic cleanup, and observability for eviction.
- [ ] Make cancellation interrupt or close an in-flight HTTP request where the
  transport permits it; otherwise expose the exact cancellation limitation.
- [ ] Expand error sanitization beyond OpenAI-style keys to authorization
  headers, bearer values, credential-bearing URLs, and common provider formats.
- [ ] Add a headless Linux credential backend that scopes the OpenRouter key to
  the MCP process, such as a permission-checked key file, systemd credential, or
  pluggable secret-provider hook.
- [ ] Validate safe permissions/ownership for external route files and optional
  scanner packages, with a documented override for unusual deployments.
- [ ] Add a VPS installation and upgrade guide, including SSH login-shell PATH,
  private/public Git marketplace behavior, credential choices, and verification.

## P1: bounded repository discovery and reads

- [ ] Add a read-only repository inventory tool with explicit locked roots.
- [ ] Add bounded file search with extension, path, count, byte, and result
  limits.
- [ ] Add bounded text search using structured arguments rather than arbitrary
  shell commands.
- [ ] Return path, byte count, content hash, and truncation metadata for every
  selected input.
- [ ] Define explicit treatment for submodules, sparse checkouts, ignored files,
  generated files, worktrees, and nested repositories.
- [ ] Preserve current protections against traversal, absolute/UNC/device paths,
  alternate data streams, symlinks, junctions, reparse points, and hard links.
- [ ] Add time-of-check/time-of-use tests for files changed during selection and
  transmission.
- [ ] Add user-configurable include/exclude policies without accepting raw glob
  patterns that can escape the locked root.

## P1: patch proposals without writes

- [ ] Define a structured patch-proposal schema with exact base-file hashes.
- [ ] Parse and validate unified diffs without invoking a shell or trusting model
  paths.
- [ ] Reject binary patches, renames outside policy, path traversal, unsupported
  modes, oversized hunks, and unexpected files.
- [ ] Require every proposed change to reference the exact reviewed snapshot.
- [ ] Return a bounded diff preview and a manifest hash without modifying the
  checkout.
- [ ] Support revision/follow-up of a proposal while retaining its provenance.

## P1: isolated patch application

- [ ] Create and verify an isolated Git worktree or equivalent staging area for
  every write-capable job.
- [ ] Resolve and validate the repository, Git directory, worktree path, base
  revision, and destination before any mutation.
- [ ] Prevent writes to the primary checkout and unrelated worktrees.
- [ ] Apply only a previously validated, hash-bound patch proposal.
- [ ] Detect conflicts and base-file changes before application.
- [ ] Record the resulting tree, diff, changed-file hashes, and untracked files.
- [ ] Add TTL and recoverable cleanup for abandoned worktrees.

## P1: allowlisted build and test execution

- [ ] Define project-owned command templates with executable and positional
  arguments represented as arrays, never arbitrary shell strings.
- [ ] Validate the executable path and every argument against the selected
  template.
- [ ] Add working-directory, environment-variable, network, CPU, memory,
  process-count, timeout, and output-size controls.
- [ ] Default test execution to the isolated worktree.
- [ ] Prevent command substitution, shell metacharacter interpretation, response
  files, and interpreter escape paths unless explicitly supported.
- [ ] Stream bounded progress while retaining a deterministic final result.
- [ ] Distinguish test failure, infrastructure failure, timeout, cancellation,
  and policy rejection.
- [ ] Capture command, exit code, duration, bounded output, and environment-policy
  metadata without logging secrets.

## P1: approval, merge, and rollback

- [ ] Present the exact diff, test evidence, file hashes, and manifest hash before
  requesting approval.
- [ ] Bind approval to one immutable proposal and result manifest.
- [ ] Require separate approval to merge or copy changes into the primary
  checkout.
- [ ] Refuse approval reuse after any file, base revision, route, model, provider,
  command, or test result changes.
- [ ] Detect a dirty primary checkout and preserve unrelated user changes.
- [ ] Provide a recoverable rollback path and document what cannot be rolled
  back.
- [ ] Never push, open a pull request, deploy, or publish without distinct user
  authorization.

## P1: adversarial tests and security review

- [ ] Publish a versioned threat model covering assets, trust boundaries,
  principals, attacker capabilities, abuse cases, and accepted residual risks.
- [ ] Add prompt-injection fixtures inside source, documentation, issue text,
  logs, test output, generated patches, and repository instructions.
- [ ] Test attempts to request secrets, expand roots, change providers, bypass
  approvals, invoke shell commands, and alter the coordinating objective.
- [ ] Fuzz JSON-RPC arguments, route configuration, path normalization, archive
  formats, patch parsing, and manifest verification.
- [ ] Stress concurrent jobs, cancellation races, file mutation races, memory
  budgets, output limits, and cleanup.
- [ ] Add Windows-specific junction, reparse-point, ADS, reserved-name, and
  case-folding tests on a runner with the required privileges.
- [ ] Add Linux/macOS symlink, hard-link, mount-boundary, permission, and Unix
  socket tests.
- [ ] Add provider outage, partial response, reasoning-only response,
  finalization, malformed metadata, and guardrail-rejection tests.
- [ ] Commission an independent security review before enabling primary-tree
  writes or submitting to a public plugin directory.

## P2: model and provider operations

- [ ] Add a read-only route diagnostics command that compares configured model
  and provider slugs against OpenRouter's current endpoints and ZDR catalogues.
- [ ] Report parameter incompatibilities, guardrail exclusions, deprecations,
  context limits, and unavailable endpoints before a paid task.
- [ ] Add an optional recommendation command that combines current price,
  throughput, latency, uptime, and user weights without automatically changing
  policy.
- [ ] Keep route changes explicit and reviewable; never silently add a provider
  discovered from OpenRouter.
- [ ] Define configuration-schema migration and backward compatibility before
  introducing route schema version 2.
- [ ] Add per-host and per-project override layering with deterministic
  precedence and hashes for every layer.
- [ ] Evaluate a safe configuration reload mechanism; retain restart-only loading
  until atomic validation and active-job behavior are specified.
- [ ] Add cost estimates and per-job spending ceilings independent of the API-key
  budget.
- [ ] Add configurable reasoning/finalization policies per task class while
  preserving usable final-answer budgets.
- [ ] Detect non-empty but incomplete/truncated Responses results using status,
  `incomplete_details`, finish metadata, and token usage; support one bounded
  continuation or return an explicit partial-result state.
- [ ] Verify and document whether OpenRouter's Responses endpoint preserves the
  configured provider attempt order, including metadata order under fallback.

## P2: observability and lifecycle

- [ ] Define a machine-checkable audit retention/redaction policy before adding
  new event types or persistence.
- [ ] Add structured audit schema versions and rotation/retention controls.
- [ ] Correlate job ID, delegation ID, route hash, input manifest, provider
  attempts, finalization attempts, approvals, commands, and output manifests.
- [ ] Keep prompt, source, response, and secret content out of default audit logs.
- [ ] Add metrics for queue depth, retained bytes, provider success/failure,
  latency, token use, cost, cancellation, and expiry.
- [ ] Add optional streaming and progress events for long reviews and test runs.
- [ ] Consider encrypted persistence for resumable jobs only after defining key
  management, expiry, and deletion semantics; remain in-memory by default.

## P2: packaging, installation, and compatibility

- [ ] Make CLI, test-harness, and diagnostic output explicitly UTF-8 on Windows
  so non-ASCII model output cannot fail on a legacy console code page.
- [ ] Add automated installation tests using built wheels and fresh user-level
  tool environments on Windows, macOS, and Linux.
- [ ] Add upgrade/downgrade and running-process lock tests.
- [ ] Add a bootstrap/check command for Codex version, plugin version, PATH,
  credentials, route file, guardrail expectation, and workspace root.
- [ ] Publish to PyPI only after package ownership, trusted publishing, signed
  releases, and recovery procedures are configured.
- [ ] Evaluate the portable root `plugin.json` Agent Plugins format after local
  compatibility-manifest behavior is stable.
- [ ] Maintain a compatibility table for Codex, Python, operating systems,
  OpenRouter endpoints, and plugin manifest versions.
- [ ] Add installation guides for Windows, macOS, desktop Linux, headless Linux,
  SSH hosts, and private/public Git marketplaces.

## P3: coding-agent experience

- [ ] Add path-and-line citations to review findings and patch proposals.
- [ ] Add task decomposition and multiple independent reviewer roles without
  allowing nested uncontrolled delegation.
- [ ] Support concurrent bounded delegates with aggregate cost and memory limits.
- [ ] Add reusable review/test presets separate from security policy.
- [ ] Provide concise progress summaries and actionable recovery guidance for
  policy, provider, guardrail, and infrastructure failures.
- [ ] Add result-quality evaluations comparing external profiles with native
  Luna, Sol, and Astra task classes.

## Deferred: universal Codex plugin directory

Do not submit this project to the universal ChatGPT/Codex plugin directory until:

- [ ] The read/search, patch, isolated-write, test, approval, and controlled-merge
  capability ladder is complete.
- [ ] Resource, job, cancellation, credential, audit, and cleanup boundaries are
  enforced and stress-tested.
- [ ] Cross-platform and adversarial suites pass on supported hosts.
- [ ] A public threat model and independent security review are complete.
- [ ] Licensing, privacy, support, release, and vulnerability-reporting policies
  are complete.
- [ ] Representative external users have exercised the public Git marketplace
  alpha and their findings have been addressed.
- [ ] The plugin package meets the then-current OpenAI submission and MCP review
  requirements.

Public GitHub availability is not evidence that these directory-readiness
conditions have been met.
