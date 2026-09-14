# Repository automation policy

These rules apply to every automated agent working in this repository.

## Human-only repository governance

Automated agents must never change repository visibility between private,
internal, or public. This prohibition applies even when publication, release,
marketplace distribution, or repository administration is otherwise in scope.
Agents may inspect visibility, explain consequences, prepare code and
documentation, and ask a human owner to make the change.

Automated agents must also not perform these repository-level governance actions
without a separate explicit human instruction for the exact action:

- transfer, archive, unarchive, rename, or delete the repository;
- change ownership, organization membership, teams, collaborators, or access;
- change branch protection, rulesets, required checks, or merge policy;
- enable or disable security, vulnerability-reporting, or secret-scanning
  features;
- change repository, organization, marketplace, or provider billing;
- submit or withdraw the plugin from a public directory;
- rotate, revoke, create, or reveal credentials and signing keys.

Repository visibility is stricter than the actions above: it is always
human-only and cannot be delegated to an automated agent.

## Release boundary

This project is a public GitHub alpha. Public source availability does not mean
the plugin is ready for the universal ChatGPT/Codex plugin directory. Preserve
the capability gates and deferred directory criteria in `TODO.md`.

## MCP availability invariant

The bundled OpenRouter MCP is an auxiliary capability and must keep
`required: false` in `plugins/openrouter-delegator/.mcp.json`. A delegator
installation, configuration, file-root, or handshake failure must not prevent
Codex from starting or resuming a task.

Any change to the MCP console command, Python packaging, plugin MCP definition,
or startup initialization must pass all of these checks before release:

1. the repository test suite and plugin/skill validators;
2. a direct initialize handshake using the source environment;
3. a direct initialize handshake using the installed launcher; and
4. a fresh ephemeral Codex task with the installed plugin enabled.

Use `docs/troubleshooting.md` for the exact recovery and smoke-test commands.
