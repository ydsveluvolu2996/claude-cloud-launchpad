# Claude Cloud Launchpad

[![Installation smoke test](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/actions/workflows/installation-smoke.yml/badge.svg?branch=main)](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/actions/workflows/installation-smoke.yml)

A beginner-friendly way to add AWS, Terraform, collaboration, and design tools to Claude Code on **macOS or Windows**. Choose the tools you need, run setup, and check that they work.

[Download v1.0.0](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/releases/tag/v1.0.0) · [MIT license](LICENSE) · [Tested versions](docs/tested-versions.md)

![A real diagnostic run checking Claude Code, installed plugins, and the pricing connector.](docs/images/demo.gif)

*Replay of real diagnostic output from an isolated Mac installation, paced for readability. [Read the accessible text output](docs/demo-output.txt). This checks installation and the pricing connection; it does not demonstrate authenticated cloud operations.*

[Start here](#start-here) · [macOS](#install-on-macos) · [Windows](#install-on-windows) · [Check setup](#check-my-setup) · [Examples](docs/examples.md) · [Remove tools](docs/removal.md) · [Help](#get-help-or-contribute)

## Start here

You will install a few basic apps, sign in to Claude Code, and run one setup script. The default **Full** setup adds **nine plugins** and an **AWS Pricing Calculator connector**. You can choose a smaller setup below. A plugin gives Claude extra capabilities; a connector, also called an MCP server, lets it work with another tool or service.

**You need:** an internet connection and an account or provider configuration that can use Claude Code. The **Claude Code terminal app** is required; using the Claude website or installing Claude Desktop alone does not guarantee that the `claude` terminal command is available.

Choose **one** guide below. You can connect AWS, GitHub, Slack, and other services later, when you need them. Each person uses their own accounts and credentials.

**Cost:** Launchpad's installer is free to use under the MIT license. Claude Code access and any third-party services you use have their own account requirements, limits, and charges. Installing Launchpad does not create AWS resources.

**How to follow this guide**

- A terminal is the app where you type commands. On a Mac, use **Terminal**. On Windows, use **PowerShell** first and then **Git Bash**, as labelled below.
- Copy commands from the text boxes, one line at a time. Press **Enter** after each line and wait for it to finish.
- Commands such as `git clone` go in your terminal. Commands beginning with `/`, such as `/plugin`, go **inside Claude Code**.
- The pictures are illustrated overviews. Use the selectable command text below them for installation.

## Choose your tools

A **profile** is a group of tools to install. At the final step of either guide, run **one** of these commands:

| What you want | Command | What it adds |
|---|---|---|
| Everything | `bash install.sh` | All nine plugins and the pricing connector |
| AWS and Terraform | `bash install.sh --profile aws` | Five plugins and the pricing connector |
| GitHub, Slack, Atlassian, and design | `bash install.sh --profile collaboration` | Five plugins; no pricing connector |

The guides use Full setup. To choose a smaller profile, replace their final `bash install.sh` line with the command above. All profiles include `session-report`. You can add another profile later; doing so adds its tools and keeps the tools you already have. See [the full list](#whats-included).

Before installing anything, the script checks that its required apps are available. It changes Claude settings for your **user account**, so installed tools are available from other project folders too.

## Install on macOS

![Illustrated macOS setup: install Git and Node.js, open Terminal, install Claude Code, sign in, run setup, and verify.](docs/images/install-macos.png)

### Step 1 — Open Terminal and install Git

Press **Command + Space**, type **Terminal**, and press **Return**.

In **Terminal**, run:

```bash
xcode-select --install
```

If a macOS installation window appears, follow its instructions and wait for it to finish. This installs Apple's command-line tools, including Git. If it says the tools are already installed, continue. See [Apple's installation guide](https://developer.apple.com/documentation/xcode/installing-the-command-line-tools) if you get an error.

### Step 2 — Install Node.js

Open [nodejs.org/download](https://nodejs.org/en/download), select a current **LTS** version and **macOS**, and download the **Installer (.pkg)** for your Mac. Open the downloaded file and follow the installer. Node.js includes `npm` and `npx`, which the pricing connector needs.

### Step 3 — Install Claude Code

In **Terminal**, paste the [official Claude Code installation command](https://code.claude.com/docs/en/setup#install-claude-code):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

If you already have a current Claude Code terminal installation, you can skip that command.

**Close Terminal and open a new Terminal window.** Run each check:

```bash
git --version
node --version
npx --version
claude --version
```

**What success looks like:** every command prints a version number. If any says “command not found,” stop and use [Troubleshooting](#troubleshooting) before continuing.

### Step 4 — Sign in

In **Terminal**, run:

```bash
claude
```

Follow the sign-in instructions. A browser may open; complete sign-in there, then return to Terminal. When Claude is ready, type **`/exit` inside Claude Code** and press Enter to return to the regular terminal.

### Step 5 — Download and run this setup

In **Terminal**, run:

```bash
cd "$HOME"
git clone --branch v1.0.0 --single-branch https://github.com/ydsveluvolu2996/claude-cloud-launchpad.git
cd claude-cloud-launchpad
bash install.sh
```

The first command goes to your home folder. The next downloads the **v1.0.0 release** into a new `claude-cloud-launchpad` folder. The last installs Full setup for your user account. Git may display “detached HEAD”: that is normal when downloading a fixed release. You do not need to change it.

**What success looks like:** the final summary says **`Done. Setup completed.`** You will also see a list of next steps. If it says **`Finished with errors`**, use the error message and the troubleshooting table below, then retry.

Continue to [Check my setup](#check-my-setup).

## Install on Windows

![Illustrated Windows setup: install Git and Node.js, install Claude in PowerShell, open Git Bash, sign in, run setup, and verify.](docs/images/install-windows.png)

### Step 1 — Install Git for Windows and Node.js

1. Download the **standalone installer** from [Git for Windows](https://git-scm.com/install/windows). Run it using its default options. This includes an app called **Git Bash**.
2. Open [nodejs.org/download](https://nodejs.org/en/download), select a current **LTS** version and **Windows**, and download the **Installer (.msi)** for your computer. Run it with the default options, including **Add to PATH**.

“PATH” lets your terminal find an installed app by its name. You do not need to edit it manually if the installers configure it correctly.

### Step 2 — Install Claude Code in PowerShell

Open the **Start menu**, type **PowerShell**, and open it. A normal PowerShell window is sufficient; you do not need “Run as administrator” for the Claude installer.

In **PowerShell**, run the [official Windows installation command](https://code.claude.com/docs/en/setup#set-up-on-windows):

```powershell
irm https://claude.ai/install.ps1 | iex
```

If you already have a current Claude Code terminal installation, you can skip that command.

### Step 3 — Switch to Git Bash

**Close your terminal windows.** Open the **Start menu**, search for **Git Bash**, and open it. Use **Git Bash for the rest of the basic setup**.

Run each check in **Git Bash**:

```bash
git --version
node --version
npx --version
claude --version
```

**What success looks like:** every command prints a version number. If a command is missing, fix it using [Troubleshooting](#troubleshooting) before continuing.

### Step 4 — Sign in

In **Git Bash**, run:

```bash
claude
```

Complete the sign-in prompts, including any browser step. Return to Git Bash, then type **`/exit` inside Claude Code** and press Enter to return to the regular terminal.

### Step 5 — Download and run this setup

Run these commands in **Git Bash**, not PowerShell:

```bash
cd "$HOME"
git clone --config core.autocrlf=false --branch v1.0.0 --single-branch https://github.com/ydsveluvolu2996/claude-cloud-launchpad.git
cd claude-cloud-launchpad
bash install.sh
```

The clone command downloads **v1.0.0** and keeps the script's line endings compatible with Bash. Keep it exactly as shown. Git may display “detached HEAD”: that is normal for a fixed release.

**What success looks like:** the final summary says **`Done. Setup completed.`** If it says **`Finished with errors`**, use the error details below it or in the preceding output to fix the problem, then retry.

Continue to the next section.

## Check my setup

Stay in the `claude-cloud-launchpad` folder, in **Terminal or Git Bash**. Run the command for the profile you installed:

| Your installation | Check command |
|---|---|
| Full | `bash doctor.sh` |
| AWS | `bash doctor.sh --profile aws` |
| Collaboration | `bash doctor.sh --profile collaboration` |

The checker reports which prerequisites and selected plugins are ready. For Full and AWS, it also checks the user-scoped pricing connection. Its first connection may take longer while `npx` downloads the pricing package. Follow the next-step message for anything marked as needing setup, then run the check again.

The checker does not install plugins or edit your configuration. Connecting the pricing server can download its pinned package into npm's cache. It does not call cloud tools, make model requests, or sign in to your accounts. A successful check covers basic setup; optional service accounts still need the configuration below.

## Try your first session

Use **Terminal on macOS** or **Git Bash on Windows**. These commands create a practice folder and start Claude there:

```bash
mkdir -p "$HOME/claude-practice"
cd "$HOME/claude-practice"
claude
```

If Claude asks whether you trust this folder, review the prompt. This is the practice folder you just created.

**Inside Claude Code**, enter these commands separately:

```text
/plugin
/mcp
```

- **`/plugin`** shows installed plugins. Check that the plugins for your chosen profile in [What's included](#whats-included) are listed.
- **`/mcp`** shows connectors and whether they are connected or need configuration. For Full or AWS, find `aws-pricing-calculator`. Collaboration setup does not add it.
- Optional services may show as disconnected until you install their extra software or sign in. Follow [Connect the tools you need](#connect-the-tools-you-need) for those features.

### Prompts you can try

Type one of these **inside Claude Code** in your own words:

> Explain the difference between EC2, S3, and Lambda using a simple website example. Do not create or change any cloud resources.

> Use the design plugin to review this page text for clarity and accessibility: [paste your sample text].

> Use AWS Pricing Calculator to draft an estimate for a small test website. Ask me about region, usage, and budget first. Do not deploy anything.

The calculator estimates costs; creating an estimate does not create AWS resources. Real cloud operations require your own AWS account configuration and permissions.

Follow the [three worked examples](docs/examples.md) for a cost estimate, a Terraform explanation, and a design review. Each includes prerequisites, a copyable prompt, and an illustrative result to help you judge the response.

### How to open it next time

Open **Terminal** or **Git Bash**, go to the folder you want to work in, and run `claude`. You do not need to rerun the installer for every session.

For the same practice folder:

```bash
cd "$HOME/claude-practice"
claude
```

## Connect the tools you need

**Basic setup is complete when the checker passes for your chosen profile.** Set up the following only for the features you plan to use.

| I want to use… | What to do next |
|---|---|
| AWS Pricing Calculator | Keep Node.js and `npx` available. The default calculator workflow does not need AWS credentials. |
| AWS tools | Install [uv](https://docs.astral.sh/uv/getting-started/installation/) so `uvx` is available, use a supported Python 3 installation, and configure your own AWS account/profile. Start with read-only permissions. |
| Terraform tools | Install [Docker](https://docs.docker.com/get-started/get-docker/) and start Docker Desktop. Configure Terraform service credentials if your workflow needs them. |
| GitHub tools | The bundled plugin requires your own `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable in the terminal that launches Claude. Follow the [plugin configuration](https://github.com/anthropics/claude-plugins-official/blob/main/external_plugins/github/.mcp.json) and [GitHub's token guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens); request only the permissions you need. |
| Slack or Atlassian | Open `/mcp` inside Claude, select the relevant connector, and follow its sign-in instructions using your workspace/site account. |
| AWS DevSecOps tools | Follow the plugin's [service setup instructions](https://github.com/aws/agent-toolkit-for-aws/tree/main/plugins/aws-agents-for-devsecops). |
| Architecture diagrams | Expand the optional diagram setup below. Its validation hook needs extra local tools. |

Some plugins, including design, include optional connectors. Configure the ones you use and disable unused connectors through Claude Code's supported settings.

**Keep credentials private.** Use your own accounts, keep permission prompts enabled, and never put tokens or AWS keys into this repository, issues, or screenshots. This installer does not grant or enforce AWS permissions.

<details>
<summary><strong>Optional: architecture diagrams and Windows WSL setup</strong></summary>

The upstream [diagram validation hook](https://github.com/awslabs/agent-plugins/blob/fbefb3764e67558fe10ac834dd85db49734aa9b6/plugins/deploy-on-aws/scripts/validate-drawio.sh) runs **`python3`** and **GNU `timeout`**. It also needs `defusedxml>=0.7.1` installed in that Python environment. Having only a `python` command is insufficient.

### macOS diagrams

Install a supported [Python 3 release](https://www.python.org/downloads/) and [Homebrew](https://brew.sh/) if needed. In **Terminal**:

```bash
brew install coreutils
export PATH="$(brew --prefix coreutils)/libexec/gnubin:$PATH"
python3 -m venv "$HOME/.venvs/claude-cloud-launchpad"
source "$HOME/.venvs/claude-cloud-launchpad/bin/activate"
python3 -m pip install "defusedxml>=0.7.1"
python3 -c "import defusedxml; print('defusedxml OK')"
timeout --version
claude
```

A virtual environment keeps these Python packages separate from your system Python. In a new terminal, repeat the `export PATH` and `source` lines before launching Claude for diagram work.

### Windows diagrams using WSL 2

For diagram validation on Windows, use **WSL 2**, a Linux environment inside Windows. Follow [Microsoft's WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install) first.

Open your **Ubuntu/WSL terminal** and install Linux Git, Node.js, Claude Code, and uv there. Windows-native installations and credentials are separate. Run this repository's clone and `bash install.sh` commands inside WSL too.

Then, in the **Ubuntu/WSL terminal**:

```bash
sudo apt update
sudo apt install python3 python3-venv coreutils
python3 -m venv "$HOME/.venvs/claude-cloud-launchpad"
source "$HOME/.venvs/claude-cloud-launchpad/bin/activate"
python3 -m pip install "defusedxml>=0.7.1"
python3 -c "import defusedxml; print('defusedxml OK')"
timeout --version
claude
```

Native Git Bash remains suitable for the basic installation. Its diagram hook additionally needs a working `python3` with `defusedxml` and GNU `timeout`; Windows' built-in `timeout.exe` is not equivalent. In a new WSL terminal, reactivate the Python environment before using diagrams.

</details>

## What's included

| Plugin or connector | What it helps with | Profiles |
|---|---|---|
| `aws-core` | AWS APIs, infrastructure, containers, monitoring, and billing | AWS, Full |
| `aws-agents-for-devsecops` | Investigations, release readiness, and vulnerability scans | AWS, Full |
| `deploy-on-aws` | Architecture diagrams and cost estimates | AWS, Full |
| `terraform` | Terraform provider and module documentation | AWS, Full |
| `github` | Repositories, pull requests, and issues | Collaboration, Full |
| `atlassian` | Jira and Confluence | Collaboration, Full |
| `slack` | Channels and conversations | Collaboration, Full |
| `session-report` | Claude Code usage and cost reports | All |
| `design` | Design critique, UX writing, accessibility, and handoff | Collaboration, Full |
| `aws-pricing-calculator` (MCP connector) | AWS Pricing Calculator estimates and shareable links | AWS, Full |

The exact plugin IDs and profile membership live in [profiles.json](profiles.json). Choosing a smaller profile does not remove plugins installed previously; use the [selective removal guide](docs/removal.md) when you want to stop using a tool.

## Troubleshooting

| What you see | What to do |
|---|---|
| “Command not found” or “not recognized” | Install the named app, close the terminal, and open a new one. Repeat the version checks. For `claude`, see [Claude's PATH troubleshooting](https://code.claude.com/docs/en/troubleshooting). |
| `irm` is not recognized | The Windows Claude install command belongs in **PowerShell**, not Git Bash or Command Prompt. |
| `bash` is not recognized in PowerShell | Open **Git Bash** from the Start menu and continue there. |
| “Destination path … already exists” when cloning | You already have a folder with that name. If it is this setup, enter `cd "$HOME/claude-cloud-launchpad"` and use the update steps below. Do not delete a folder containing your own work. |
| Errors mentioning `\r` or `^M` on Windows | Use a fresh clone with `--config core.autocrlf=false`, as shown in the Windows guide. |
| A prerequisite is missing, or setup finishes with errors | Follow the named app's installation step above, reopen the terminal, then retry your chosen profile. Run `bash doctor.sh` with the same profile to find what still needs attention. |
| A connector is disconnected | Open `/mcp` in Claude. Check its sign-in and prerequisites: Terraform needs running Docker; AWS tools need `uvx`. |
| Pricing works only in one project folder | A project may have its own connector settings. Run the checker from this release and inspect `/mcp` in the affected project; user and project settings can differ. |
| GitHub authentication fails | Ensure your own `GITHUB_PERSONAL_ACCESS_TOKEN` is available to the terminal that launches Claude. Never paste it into an issue. |
| Diagram validation fails | Use the optional diagram guide and verify `python3` can import `defusedxml`, and `timeout --version` identifies GNU coreutils. |

To retry Full setup, first type `/exit` if you are inside Claude. Then, in **Terminal or Git Bash**:

```bash
cd "$HOME/claude-cloud-launchpad"
bash install.sh
```

If you chose AWS or Collaboration, add the same `--profile aws` or `--profile collaboration` to both installer and checker commands.

## Update or remove this setup

The beginner guides install a fixed release. Check [Releases](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/releases) and read the next version's notes before updating. A Git tag pins Launchpad's files; it does **not** pin marketplace plugin versions or the Claude Code app.

To return to the published v1.0.0 files, run these commands in **Terminal or Git Bash**:

```bash
cd "$HOME/claude-cloud-launchpad"
git status --short
```

If that prints changed files, save your work before switching releases. When the working folder is clean:

```bash
git fetch --tags origin
git checkout --detach v1.0.0
bash install.sh
bash doctor.sh
```

For a future release, replace `v1.0.0` with the exact published tag from its release notes. Add your chosen `--profile` to the last two commands if you use a smaller setup. Do not use `git pull` while checked out at a release tag.

To update installed plugin versions, use the update controls in `/plugin` inside Claude. The pricing package is deliberately pinned to `sample-aws-pricing-calculator-mcp@1.3.4`; rerunning setup preserves an existing user-scoped pricing-server configuration. Read future release notes for any connector migration instructions.

To pause a plugin, remove selected tools, or recover from a failed setup, follow [Remove tools and recover](docs/removal.md). Deleting the downloaded folder alone does not uninstall user-scoped plugins.

## Compatibility and test coverage

| Environment | What has been checked |
|---|---|
| Apple silicon Mac, macOS 26.6.2 | Real installation and repeat installation in native CI |
| Apple silicon Mac, macOS 27.2 | Real installation in a separate local test profile |
| Windows Server 2025 x64 with Git Bash | Real native Windows installation and repeat installation in CI |
| Windows 11 desktop | Not yet verified by this project with a beginner walkthrough |
| Intel Mac | Not yet verified by this project |
| Linux / WSL 2 and optional diagram tooling | Instructions are included where relevant; this release does not claim those paths were tested end to end |

See the [tested version record](docs/tested-versions.md) for the release evidence and [current automated results](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/actions/workflows/installation-smoke.yml) for later upstream changes. A passing installation check does not verify your AWS, GitHub, Slack, or Atlassian account access.

## Get help or contribute

- Start with [Troubleshooting](#troubleshooting) and [Check my setup](#check-my-setup).
- For an installation problem, [open a bug report](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/issues/new?template=bug_report.yml) with your OS, versions, chosen profile, and a sanitized error message.
- For an improvement, [request a feature](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/issues/new?template=feature_request.yml) or read [Contributing](CONTRIBUTING.md).
- For a vulnerability or exposed credential, use the [private security-reporting instructions](SECURITY.md).

Community support covers this repository's installer, checker, and documentation. Account billing, organization policies, and bugs inside upstream tools may need their provider's support. Maintainers respond as availability permits.

Launchpad is an independent community project, not an official Anthropic or AWS product. Original project files are [MIT licensed](LICENSE); upstream plugins and services keep their own licenses and terms. See [Credits](CREDITS.md), [Changelog](CHANGELOG.md), and our [Code of Conduct](CODE_OF_CONDUCT.md).

<details>
<summary><strong>Technical details, validation, and official references</strong></summary>

### Where settings apply

- `install.sh` installs plugins and the pricing server at **user scope**, so they can be used in other project folders.
- `profiles.json` selects tools explicitly. This release does not ship project-scoped plugin settings or an MCP override that silently enables a different profile.
- Your own projects may have settings that take precedence over user settings; inspect `/plugin` and `/mcp` in the project where you work.
- Existing user-scoped pricing-server settings are preserved. To inspect them, run `claude mcp get aws-pricing-calculator` from outside this checkout; this may start a server connection check.
- Current Claude Code supports plain `npx` on native Windows; the old `cmd /c` workaround is not required.

### What has been checked

The [installation workflow](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/actions/workflows/installation-smoke.yml) tests **real installations on native macOS and native Windows with Git Bash**. Open the latest run to see its result, platform details, and tool versions.

Each job uses a fresh Claude profile and npm cache, installs the official Claude Code CLI and current Node.js LTS, then checks:

- Selected plugins are installed and enabled at user scope, with their files present.
- For Full and AWS, the pinned pricing connector is saved in the user profile.
- For Full and AWS, the actual pricing server responds to MCP initialization and lists its tools.
- Claude can connect to the pricing server using the registered `npx` command from a different folder.
- Collaboration setup does not add the pricing connector.
- Running the installer again succeeds and preserves the existing pricing configuration.

Isolated failure-path tests supplement the real installation checks, including missing prerequisites, profile selection, and paths containing spaces. Verification logs are available as workflow artifacts. The installer and checker return a nonzero status when a required step fails.

These checks do not sign in to your service accounts, make model API calls, deploy resources, or invoke cloud tools. AWS, GitHub, Slack, Atlassian, Terraform, and optional diagram dependencies still need the feature-specific setup described above. A passing installation test does not certify those authenticated integrations for your accounts.

### Official references

- [Claude Code installation](https://code.claude.com/docs/en/setup)
- [Plugin installation and scopes](https://code.claude.com/docs/en/discover-plugins)
- [MCP configuration](https://code.claude.com/docs/en/mcp)
- [Official plugin catalog](https://github.com/anthropics/claude-plugins-official/blob/main/.claude-plugin/marketplace.json)
- [Knowledge-work design plugin](https://github.com/anthropics/knowledge-work-plugins/tree/main/design)
- [AWS Pricing Calculator MCP](https://github.com/aws-samples/sample-aws-pricing-calculator-mcp)
- [Claude Code changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)

</details>
