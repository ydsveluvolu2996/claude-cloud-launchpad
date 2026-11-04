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
python3 tests/test_release.py
git diff --check
```

On Windows, use `python` instead of `python3` if that is the Python command provided by your installation.

The isolated tests use simulated commands and temporary files. They must not install real plugins, read credentials, or change your normal Claude profile.

Real integration tests run in the [installation workflow](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/actions/workflows/installation-smoke.yml) with a separate Claude profile and npm cache. They install external packages and connect the pricing server, but do not call cloud tools or make model requests. Use those workflow results for cross-platform changes. Never run `scripts/verify_installation.py` against a personal Claude profile.

For docs-only changes, check links, command syntax, and whether the instructions make sense from a fresh terminal. For installer changes, cover success, failure, repeat installation, selected profile behavior, and paths containing spaces. State any environment you could not test.

## Release practice

A release records Launchpad's tag, tested tool versions, test-run links, and known limitations. Marketplace contents can change independently of this repository. Keep changes on a pull request until the required checks pass; do not edit an already-published release tag.

Maintainers publish through the manual [Publish release workflow](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/actions/workflows/release.yml):

1. Update `VERSION`, the changelog, and release documentation in a pull request. Merge only after the required checks pass.
2. Wait for both **Installation smoke test** and **Repository checks** to succeed on `main` for the exact commit being released. Copy each run's numeric ID from its URL, such as the number after `/actions/runs/`. A successful run for an older commit is not sufficient.
3. Open **Actions → Publish release → Run workflow** and select **main**. Set `tag` to the matching version tag (for example, `v1.0.0`), `installation_run_id` to that main installation run, and `checks_run_id` to that main repository-checks run. If `main` advances before dispatch, wait for successful runs for the new commit and use those IDs.
4. The workflow verifies the commit and test evidence, including all eight required jobs and twelve installation reports. It builds ZIP and tar archives plus checksums, uploads them to a draft release, and downloads the uploaded assets to verify their bytes before publishing the release as latest.
5. Check the completed workflow, release notes, download links, and published assets. The custom ZIP contains a versioned project folder such as `claude-cloud-launchpad-1.0.0`, with `install.sh`, `doctor.sh`, and `profiles.json` at its top level.

A failed validation must be fixed before publication. Do not manually publish a draft that the workflow left behind after a failed check. Re-run the workflow with valid evidence once the cause is resolved. Changes to release packaging should pass `python3 tests/test_release.py` as well as the repository checks.

Contributions to original Launchpad files are provided under this repository's [MIT license](LICENSE). Preserve upstream notices when a contribution includes third-party material.
