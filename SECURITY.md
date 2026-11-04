# Security reporting

## Report privately

If you find a vulnerability in Launchpad, use [Report a vulnerability](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/security/advisories/new) on GitHub. You need a GitHub account. Do not open a public issue containing exploit details or credentials.

Include the affected release, operating system, reproduction steps, expected behavior, and a small sanitized example. Explain what an attacker could do. Do not send live tokens, passwords, AWS keys, private configuration files, or customer data.

If a credential has already been exposed, revoke or rotate it through the service that issued it. Removing a public post does not invalidate a credential.

## Scope and supported versions

Security fixes target the latest stable Launchpad release; older releases may require an update. For v1, use the newest published v1 release. There is no guaranteed response or resolution time; maintainers will respond as availability permits.

Launchpad maintains the installer, diagnostic checker, profile selection, and documentation in this repository. Claude Code, marketplace plugins, MCP packages, and hosted services are maintained upstream. Report a vulnerability in an upstream component through that project's security policy, and privately let us know if it affects Launchpad users.

## Intended behavior

The installer writes user-scoped Claude plugin and pricing-connector configuration. The checker inspects selected components and may start the pricing connector to verify its connection. Neither script should request cloud credentials, disable permission prompts, or deploy resources. External plugins can perform actions permitted by their own configuration and your accounts.

For ordinary setup errors, use the [bug-report form](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/issues/new?template=bug_report.yml) with sanitized output.
