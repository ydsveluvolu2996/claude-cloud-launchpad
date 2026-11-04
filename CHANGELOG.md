# Changelog

## v1.0.0 — 2026-11-04

First public release of Claude Cloud Launchpad.

### Added

- Full, AWS, and Collaboration installation profiles with explicit tool membership.
- Prerequisite checks before installation starts and a beginner-facing `doctor.sh` checker.
- Illustrated macOS and Windows installation instructions, a recorded diagnostic demo, and three worked examples.
- Selective removal and recovery instructions that preserve unrelated Claude configuration.
- A compatibility table and a tested-version record with links to installation evidence.
- Isolated regression tests and native macOS/Windows installation checks, including repeat installation and a live pricing-server connection.
- MIT licensing, upstream credits, contribution guidance, issue forms, a code of conduct, and private security-reporting instructions.

### Behavior

- Installs selected plugins at user scope. Full and AWS also configure `sample-aws-pricing-calculator-mcp@1.3.4`.
- Keeps an existing user-scoped pricing configuration instead of overwriting it.
- Uses `profiles.json` as the source of tool membership. This release does not silently enable all tools through project-scoped settings in the checkout.
- Returns a failing exit status when a required installation or diagnostic check fails.

### Known limits

- Windows CI runs on Windows Server 2025 with Git Bash. Windows 11 beginner walkthroughs, Intel Macs, and the WSL/diagram path are not yet verified end to end by this project.
- Installation checks do not authenticate to personal service accounts, make model API calls, deploy resources, or exercise cloud tools.
- Marketplace plugins and Claude Code can update independently. The release tag fixes Launchpad's files, not external marketplace contents. See [tested versions](docs/tested-versions.md).
- Switching to a smaller profile does not remove previously installed tools. Use [selective removal](docs/removal.md) when needed.
