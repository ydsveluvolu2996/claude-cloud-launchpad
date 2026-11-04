# What v1.0.0 tests

The [v1.0.0 release](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/releases/tag/v1.0.0) includes a permanent **[tested-versions.json](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/releases/download/v1.0.0/tested-versions.json)** attachment with the tested commit, workflow links, operating systems, Claude Code and Node.js versions, and every installed plugin version. The release notes link to the actual test results.

## Coverage

| Environment | Release validation |
|---|---|
| Native macOS on Apple silicon | AWS, Collaboration, and Full profiles; fresh install, doctor, and repeat install |
| Native Windows Server 2025 with Git Bash | The same three profiles and checks; this is a Windows runner, not WSL |
| macOS 27.2 on Apple silicon, local isolated profile | Full installer, doctor, live pricing protocol, and unchanged personal Claude settings; Claude Code 2.1.318 and Node.js v24.18.0 |
| Windows 11 desktop, Intel Mac | Not yet directly tested by this project |
| WSL 2, diagram hooks, account-authenticated integrations | Separate setup documented; not covered by the installation tests |

The local [demo transcript](demo-output.txt) records the actual doctor output from the local Mac test. The animation replays that output at a readable pace; it is not a screen recording or an authenticated cloud-service demonstration.

## What a passing check means

- Each fresh profile contains exactly its selected, enabled, user-scoped plugins with their files present.
- AWS and Full save the pinned pricing registration, connect through Claude from outside the repository, and complete a live MCP initialize/tools-list exchange without invoking a cloud tool.
- Collaboration installs no pricing registration.
- A second installation succeeds and keeps the pricing configuration unchanged where applicable.
- Source, configuration, and cache paths containing spaces are exercised in native CI.
- Isolated simulated tests cover prerequisites, failures, profile selection, existing settings, and readable diagnostic errors.

The tests use isolated Claude settings and caches. They do not sign in to service accounts, send model requests, or create cloud resources. A successful installation does not verify a person's AWS, GitHub, Slack, Atlassian, or Terraform account access.

## Versions can change independently

The pricing package is pinned to `sample-aws-pricing-calculator-mcp@1.3.4`. Marketplace plugins and the official Claude installer are maintained upstream. A Launchpad tag fixes this repository's scripts and documentation, but does not freeze those external downloads. The version record describes what was tested, not a lockfile.

The [installation workflow](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/actions/workflows/installation-smoke.yml) also runs weekly and on pull requests to catch changes upstream. Its temporary artifacts contain fresh and repeated-install logs plus version records. GitHub Actions dependency updates are proposed by Dependabot; they do not automatically upgrade marketplace plugins on users' machines.
