# Remove tools and recover

Launchpad installs tools for your Claude **user account**. Removing one affects other project folders that use that user-scoped installation too. Launchpad does not track whether you already used a plugin or pricing connector before setup, so choose components individually.

Use **Terminal on macOS** or **Git Bash on Windows** for every command below. If you are inside Claude Code, type `/exit` first.

## 1. Inspect before changing anything

Run:

```bash
claude plugin list
```

Check the plugin name and scope. Only the `user` entries listed in [Launchpad's tool table](../README.md#whats-included) are relevant here. You can also inspect installed plugins through `/plugin` inside Claude.

If you installed Full or AWS, inspect the pricing connector:

```bash
cd "$HOME"
claude mcp get aws-pricing-calculator
```

This can start a connection check. Review the reported scope and configuration privately. Keep an existing connector you still use; setup intentionally preserves pre-existing user configuration.

## 2. Pause a plugin first, if you are unsure

For example, to pause the design plugin without uninstalling it:

```bash
claude plugin disable design@knowledge-work-plugins --scope user
```

To turn it back on:

```bash
claude plugin enable design@knowledge-work-plugins --scope user
```

Restart Claude Code afterward. If Claude says another plugin depends on it, review that relationship before changing the dependent plugin. See the [official plugin command reference](https://code.claude.com/docs/en/plugins/cli-reference#plugin-disable).

## 3. Remove only the plugins you choose

Run a command only for a plugin you no longer want. `--keep-data` retains its persistent data directory. It does **not** guarantee retention of the plugin's saved options or secrets when you remove its final installed scope; save any information you need privately first. See [what uninstall keeps](https://code.claude.com/docs/en/plugins/cli-reference#what-an-uninstall-deletes-and-keeps).

| Plugin | Command |
|---|---|
| AWS core | `claude plugin uninstall aws-core@claude-plugins-official --scope user --keep-data` |
| AWS DevSecOps | `claude plugin uninstall aws-agents-for-devsecops@claude-plugins-official --scope user --keep-data` |
| Deploy on AWS | `claude plugin uninstall deploy-on-aws@claude-plugins-official --scope user --keep-data` |
| Terraform | `claude plugin uninstall terraform@claude-plugins-official --scope user --keep-data` |
| GitHub | `claude plugin uninstall github@claude-plugins-official --scope user --keep-data` |
| Atlassian | `claude plugin uninstall atlassian@claude-plugins-official --scope user --keep-data` |
| Slack | `claude plugin uninstall slack@claude-plugins-official --scope user --keep-data` |
| Session report | `claude plugin uninstall session-report@claude-plugins-official --scope user --keep-data` |
| Design | `claude plugin uninstall design@knowledge-work-plugins --scope user --keep-data` |

A plugin may remain at another scope or remain unavailable for removal because of organization policy. Read Claude's response rather than deleting its configuration files manually.

## 4. Remove the pricing connector, if you no longer use it

For the user-scoped connector only:

```bash
claude mcp remove aws-pricing-calculator --scope user
```

This removes the registration, not any unrelated MCP server. Existing project-scoped definitions are separate. The [official MCP guide](https://code.claude.com/docs/en/mcp#managing-your-servers) explains server management.

## 5. Check the result

Restart Claude Code and inspect `/plugin` and `/mcp`. A checker for a profile whose tools you intentionally removed will report missing components; that is expected.

The marketplace catalogs, Node.js, Git, and Claude Code can remain installed because other tools may use them. If you no longer need the downloaded `claude-cloud-launchpad` folder and have saved any edits, remove that folder using Finder or File Explorer. Do not delete your entire `.claude` folder, `.claude.json`, or npm cache as a Launchpad removal step.

## Recover from a failed installation

A failed setup may leave some selected plugins installed. Fix the reported prerequisite or connection problem, then rerun the same profile. For example:

```bash
cd "$HOME/claude-cloud-launchpad"
bash install.sh --profile aws
bash doctor.sh --profile aws
```

Use `collaboration` for that profile, or omit `--profile aws` on both commands for Full. Rerunning preserves the existing pricing registration. Switching to a smaller profile adds its tools without automatically removing previous ones.

If you deliberately removed a plugin and want it back, rerun its profile. If it is installed but disabled, enable it explicitly through `/plugin` or the `claude plugin enable` command. Service sign-ins may need to be completed again after removal.
