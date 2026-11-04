#!/usr/bin/env bash
# Claude Cloud Launchpad - plugin and MCP setup
# Installs plugins and MCP servers for the current user.

set -u

OFFICIAL="claude-plugins-official"
OFFICIAL_PLUGINS=(
  aws-core
  aws-agents-for-devsecops
  deploy-on-aws
  terraform
  github
  atlassian
  slack
  session-report
)

KW_MARKETPLACE_REPO="anthropics/knowledge-work-plugins"
KW="knowledge-work-plugins"
KW_PLUGINS=(
  design
)

PRICING_NAME="aws-pricing-calculator"
PRICING_PKG="sample-aws-pricing-calculator-mcp@1.3.4"

FAILED=()

if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code is not installed. Install Claude Code first, then run this script again."
  exit 1
fi

install_plugin() {
  echo "-> $1"
  claude plugin install --scope user "$1" || FAILED+=("$1")
}

register_marketplace() {
  if ! claude plugin marketplace add --scope user "$1"; then
    echo "Could not register marketplace: $1" >&2
    FAILED+=("$1 marketplace")
    return 1
  fi
}

install_pricing_mcp() (
  # Check outside this repository so its .mcp.json cannot hide a missing user server.
  mcp_dir=$(mktemp -d "${TMPDIR:-/tmp}/claude-cloudops-mcp.XXXXXX") || {
    echo "Could not create a temporary directory for the MCP configuration check." >&2
    return 1
  }
  trap 'rm -rf -- "$mcp_dir"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  cd "$mcp_dir" || return 1

  if claude mcp get "${PRICING_NAME}" >/dev/null 2>&1; then
    echo "Already configured outside this setup repository; keeping the existing MCP server."
  else
    claude mcp add --scope user "${PRICING_NAME}" -- npx -y "${PRICING_PKG}"
  fi
)

echo "== Plugins from ${OFFICIAL} =="
if register_marketplace "anthropics/${OFFICIAL}"; then
  for p in "${OFFICIAL_PLUGINS[@]}"; do
    install_plugin "${p}@${OFFICIAL}"
  done
fi

echo
echo "== Plugins from ${KW} =="
if register_marketplace "${KW_MARKETPLACE_REPO}"; then
  for p in "${KW_PLUGINS[@]}"; do
    install_plugin "${p}@${KW}"
  done
fi

echo
echo "== AWS Pricing Calculator MCP server =="
if ! command -v node >/dev/null 2>&1 || ! command -v npx >/dev/null 2>&1; then
  echo "Node.js and npx are required. Install Node.js for your operating system, reopen your terminal, and run this script again."
  FAILED+=("${PRICING_NAME} (needs Node.js and npx)")
else
  install_pricing_mcp || FAILED+=("${PRICING_NAME}")
fi

echo
if [ ${#FAILED[@]} -eq 0 ]; then
  echo "Done. Setup completed."
else
  echo "Finished with errors. These steps failed: ${FAILED[*]}"
  echo "Review the errors above and run this script again after resolving them."
  echo "Plugins can also be installed in Claude Code: /plugin -> Discover -> Install for you (user scope)"
fi

echo
echo "Next steps:"
echo "  1. Install defusedxml>=0.7.1 with your Python 3 environment's package manager if you need architecture diagrams."
echo "  2. Restart Claude Code, then type /plugin and /mcp to check installation, connections, and any required configuration."
echo "  3. Configure service authentication as described in README.md (GitHub token, Slack, and Atlassian)."
echo "  4. Configure your own AWS credentials and use a READ-ONLY AWS profile for accounts you inspect."

if [ ${#FAILED[@]} -ne 0 ]; then
  exit 1
fi
