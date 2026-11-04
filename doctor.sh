#!/usr/bin/env bash
# Check installation without changing Claude settings or calling cloud tools.
set -u

SETUP_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd) || exit 1
SETUP_COMMAND=doctor
# shellcheck source=scripts/setup-common.sh
source "$SETUP_ROOT/scripts/setup-common.sh"
parse_options "$@" || exit $?
if [ "$SHOW_HELP" -eq 1 ]; then show_help; exit 0; fi

echo "Claude Cloud Launchpad — check $PROFILE setup"
check_prerequisites || exit 1
load_profile || exit 1
make_neutral_directory || exit 1
trap 'rm -rf -- "$NEUTRAL_DIR"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
cd "$NEUTRAL_DIR" || exit 1

failed=0
# Only report expected plugin names and a short result; never echo raw config.
if plugin_list=$(claude plugin list --json 2>/dev/null); then
  if ! printf '%s' "$plugin_list" | node -e '
const fs = require("fs");
try {
  const data = JSON.parse(fs.readFileSync(0, "utf8"));
  if (!Array.isArray(data)) throw new Error();
  let failed = false;
  for (const id of process.argv.slice(1)) {
    const matches = data.filter(p => p.id === id && p.scope === "user");
    const ok = matches.length === 1 && matches[0].enabled === true && !(matches[0].errors && matches[0].errors.length);
    console.log((ok ? "PASS " : "NEEDS SETUP ") + id.split("@")[0] + (ok ? " is installed and enabled." : " is missing, disabled, or has a load error."));
    if (!ok) failed = true;
  }
  process.exit(failed ? 1 : 0);
} catch {
  console.log("NEEDS SETUP Cannot read the installed plugin list. Update Claude Code, then try again.");
  process.exit(1);
}
' "${PLUGINS[@]}"; then
    failed=1
    echo "Fix: run bash install.sh --profile $PROFILE from the setup folder."
    echo "If a plugin is disabled or still has an error, open /plugin inside Claude Code and inspect it."
  fi
else
  echo "NEEDS SETUP Cannot list Claude plugins. Run claude --version, then update Claude Code if needed."
  failed=1
fi

if [ -n "$PRICING_NAME" ]; then
  echo "Checking the pricing connection (the first download can take a couple of minutes)..."
  # Give a cold npm cache time to download the connector; respect an explicit override.
  # This applies only to this check and does not change the user's Claude settings.
  if pricing_status=$(MCP_TIMEOUT="${MCP_TIMEOUT:-120000}" claude mcp get "$PRICING_NAME" 2>/dev/null); then
    if printf '%s' "$pricing_status" | node -e '
const fs = require("fs");
const status = fs.readFileSync(0, "utf8").replace(/\x1b\[[0-9;]*m/g, "");
process.exit(/User config/.test(status) && /Status:\s*(?:[✓✔]\s*)?Connected(?:\s|$)/.test(status) ? 0 : 1);
'; then
      echo "PASS Pricing connector is connected from outside this setup folder."
    else
      echo "NEEDS SETUP Pricing connector is saved but not connected at user scope."
      echo "Fix: open /mcp inside Claude Code, inspect aws-pricing-calculator, and check your internet connection and Node.js installation."
      failed=1
    fi
  else
    echo "NEEDS SETUP Pricing connector was not found or could not be inspected."
    echo "Fix: run bash install.sh --profile $PROFILE from the setup folder, then retry this check."
    failed=1
  fi
fi

echo
if [ "$failed" -eq 0 ]; then
  echo "Your selected Launchpad setup is ready."
  echo "Next: start Claude Code in your project. Optional services may still need your own sign-in."
  echo "See README.md → Connect the tools you need."
else
  echo "Some checks need attention. Follow the fixes above, then run this check again."
  exit 1
fi
