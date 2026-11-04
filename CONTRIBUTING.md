# Contributing

Thanks for helping make Claude Cloud Launchpad easier to use. Documentation fixes, clearer error messages, and reports from real beginner installations are useful contributions.

## Start with the right place

- Installation problem: use the [bug-report form](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/issues/new?template=bug_report.yml).
- New idea: use the [feature-request form](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/issues/new?template=feature_request.yml).
- Vulnerability or exposed credential: follow [SECURITY.md](SECURITY.md) privately.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md). Do not include tokens, passwords, account IDs, private repository names, or personal chat logs in examples or reports.

## Make a change

1. Fork this repository and clone your fork.
2. Create a branch for one clear improvement.
3. Keep beginner instructions accurate for Terminal on macOS and Git Bash on Windows.
4. Test the behavior you changed and describe the result in your pull request.
5. Open a pull request against `main` using the included template.

The release guides clone a fixed tag for users. Contributors should work from `main` in their fork. Keep `profiles.json` as the source of truth for tool membership; update documentation and tests when changing it. Explain any new dependency, service authentication requirement, or change to user settings.

## Local checks

Use a supported Python 3 installation for development tests; Python is not required for the basic installer or checker.

In the repository folder, run:

```bash
python3 scripts/check_repository.py
python3 tests/test_setup.py
git diff --check
```

On Windows, use `python` instead of `python3` if that is the Python command provided by your installation.

The isolated tests use simulated commands and temporary files. They must not install real plugins, read credentials, or change your normal Claude profile.

Real integration tests run in the [installation workflow](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/actions/workflows/installation-smoke.yml) with a separate Claude profile and npm cache. They install external packages and connect the pricing server, but do not call cloud tools or make model requests. Use those workflow results for cross-platform changes. Never run `scripts/verify_installation.py` against a personal Claude profile.

For docs-only changes, check links, command syntax, and whether the instructions make sense from a fresh terminal. For installer changes, cover success, failure, repeat installation, selected profile behavior, and paths containing spaces. State any environment you could not test.

## Release practice

A release records Launchpad's tag, tested tool versions, test-run links, and known limitations. Marketplace contents can change independently of this repository. Keep changes on a pull request until the required checks pass; do not edit an already-published release tag.

Contributions to original Launchpad files are provided under this repository's [MIT license](LICENSE). Preserve upstream notices when a contribution includes third-party material.
