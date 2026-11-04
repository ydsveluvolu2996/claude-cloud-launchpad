# Credits and licenses

Claude Cloud Launchpad is an independent community setup project. It is not an official product of, or endorsed by, Anthropic, Amazon Web Services, GitHub, Slack, Atlassian, HashiCorp, or their affiliates. Product names identify the tools this setup can work with.

Original Launchpad scripts, documentation, tests, and illustrations are provided under the [MIT license](LICENSE). Installing external tools does not change their licenses, ownership, service terms, or account requirements.

| Project | How Launchpad uses it |
|---|---|
| [Claude Code](https://code.claude.com/docs/en/overview) | The terminal app that runs the plugins and connectors |
| [Anthropic official plugin marketplace](https://github.com/anthropics/claude-plugins-official) | Catalog for eight of the nine plugins in Full setup |
| [Knowledge Work plugins](https://github.com/anthropics/knowledge-work-plugins) | Source of the design plugin |
| [AWS agent plugins](https://github.com/awslabs/agent-plugins) | Upstream AWS capabilities referenced through the marketplace |
| [Agent Toolkit for AWS](https://github.com/aws/agent-toolkit-for-aws) | Upstream AWS DevSecOps plugin and service instructions |
| [AWS Pricing Calculator MCP](https://github.com/aws-samples/sample-aws-pricing-calculator-mcp) | The pricing connector; Launchpad currently requests npm version 1.3.4 |
| [Model Context Protocol](https://modelcontextprotocol.io/) | The protocol used by connectors |

The external repositories and downloaded packages contain their applicable license notices. Claude Code downloads plugins from their upstream sources; Launchpad does not relicense them. See [profiles.json](profiles.json) for exact marketplace identifiers and [the tested version record](docs/tested-versions.md) for the release snapshot.

The setup illustrations are explanatory guides. The diagnostic demo presents output recorded from a real test installation; worked examples are labelled as instructional examples, not recorded service results.

The pinned pricing package was compared byte for byte with its upstream source; see [the verification record and limits](docs/maintenance.md#pricing-package-source-verification).
