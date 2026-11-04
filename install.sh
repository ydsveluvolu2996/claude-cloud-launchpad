#!/usr/bin/env bash
# Claude Cloud Launchpad — install selected tools for the current user.
set -u

SETUP_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd) || exit 1
SETUP_COMMAND=install
# shellcheck source=scripts/setup-common.sh
source "$SETUP_ROOT/scripts/setup-common.sh"
parse_options "$@" || exit $?
if [ "$SHOW_HELP" -eq 1 ]; then show_help; exit 0; fi

echo "Claude Cloud Launchpad — $PROFILE setup"
echo "Checking prerequisites before making changes..."
check_prerequisites || exit 1
load_profile || exit 1
make_neutral_directory || exit 1
trap 'rm -rf -- "$NEUTRAL_DIR"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
cd "$NEUTRAL_DIR" || exit 1

FAILED=()
for ((i=0; i<${#MARKET_NAMES[@]}; i++)); do
  market=${MARKET_NAMES[$i]}
  echo
  echo "== Plugins from $market =="
  if claude plugin marketplace add --scope user "${MARKET_SOURCES[$i]}"; then
    for plugin in "${PLUGINS[@]}"; do
      if [ "${plugin##*@}" = "$market" ]; then
        echo "-> $plugin"
        claude plugin install --scope user "$plugin" || FAILED+=("$plugin")
      fi
    done
  else
    echo "Could not register marketplace: ${MARKET_SOURCES[$i]}" >&2
    FAILED+=("$market marketplace")
  fi
done

if [ -n "$PRICING_NAME" ]; then
  echo
  echo "== AWS Pricing Calculator connector =="
  if claude mcp get "$PRICING_NAME" >/dev/null 2>&1; then
    echo "Already configured for your user; keeping the existing pricing connector."
  else
    claude mcp add --scope user "$PRICING_NAME" -- npx -y "$PRICING_PKG" || FAILED+=("$PRICING_NAME")
  fi
fi

echo
if [ ${#FAILED[@]} -eq 0 ]; then
  echo "Done. Setup completed."
  echo "Next: return to your setup folder and run: bash doctor.sh --profile $PROFILE"
  echo "Then restart Claude Code in your project and open /plugin and /mcp."
  echo "Follow README.md to connect only the services you want to use."
else
  echo "Finished with errors. These steps failed: ${FAILED[*]}"
  echo "Review the errors above, then run: bash install.sh --profile $PROFILE"
  echo "See README.md → Troubleshooting for help."
  exit 1
fi
