# shellcheck shell=bash disable=SC2034
# This sourced helper sets shared variables consumed by both entry scripts.
# Shared by install.sh and doctor.sh. Compatible with macOS Bash 3.2 and Git Bash.

parse_options() {
  PROFILE=full
  SHOW_HELP=0
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --help|-h) SHOW_HELP=1; shift ;;
      --profile)
        if [ "$#" -lt 2 ]; then
          echo "Choose a profile: --profile aws, --profile collaboration, or --profile full." >&2
          return 2
        fi
        PROFILE=$2
        shift 2
        ;;
      *) echo "Unknown option: $1. Run bash ${SETUP_COMMAND}.sh --help." >&2; return 2 ;;
    esac
  done
  case "$PROFILE" in
    aws|collaboration|full) ;;
    *) echo "Unknown profile: $PROFILE. Choose aws, collaboration, or full." >&2; return 2 ;;
  esac
}

show_help() {
  echo "Claude Cloud Launchpad — ${SETUP_COMMAND}"
  echo "Usage: bash ${SETUP_COMMAND}.sh [--profile aws|collaboration|full]"
  echo
  echo "  aws            AWS, Terraform, session reports, and pricing (5 plugins)"
  echo "  collaboration  GitHub, Atlassian, Slack, design, and session reports (5 plugins)"
  echo "  full           Everything (9 plugins and pricing); the default"
  echo
  if [ "$SETUP_COMMAND" = install ]; then
    echo "Adds the selected tools to your Claude user profile. Existing tools stay installed."
  else
    echo "Checks the selected tools. It does not install, remove, or change settings."
    echo "For aws/full, it connects to the pricing server without calling any cloud tools."
  fi
}

check_prerequisites() {
  local missing=0 command_name
  for command_name in git node claude; do
    if command -v "$command_name" >/dev/null 2>&1; then
      echo "PASS $command_name is available."
    else
      missing=1
      case "$command_name" in
        git) echo "NEEDS SETUP Git: follow README.md, Step 1 for your operating system." ;;
        node) echo "NEEDS SETUP Node.js: install the current LTS from https://nodejs.org/en/download, then reopen your terminal." ;;
        claude) echo "NEEDS SETUP Claude Code: follow README.md, Install Claude Code, then reopen your terminal." ;;
      esac
    fi
  done
  if [ "$PROFILE" != collaboration ] && ! command -v npx >/dev/null 2>&1; then
    echo "NEEDS SETUP npx: reinstall Node.js LTS (which includes npx), then reopen your terminal."
    missing=1
  elif [ "$PROFILE" != collaboration ]; then
    echo "PASS npx is available."
  fi
  if [ "$missing" -ne 0 ]; then
    echo "Fix the missing prerequisites above, then run this command again."
    return 1
  fi
}

load_profile() {
  local manifest kind first second
  manifest=$(node - "$SETUP_ROOT/profiles.json" "$PROFILE" <<'NODE'
const fs = require('fs');
try {
  const data = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const selected = data.profiles[process.argv[3]];
  if (!Array.isArray(selected) || !selected.length || new Set(selected).size !== selected.length) throw new Error();
  const markets = new Set();
  for (const id of selected) {
    if (typeof id !== 'string' || !/^[a-z0-9-]+@[a-z0-9-]+$/.test(id)) throw new Error();
    const market = id.split('@')[1];
    const source = data.marketplaces[market];
    if (typeof source !== 'string' || !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(source)) throw new Error();
    markets.add(market);
  }
  for (const market of markets) console.log(['M', market, data.marketplaces[market]].join('\t'));
  for (const id of selected) console.log(['P', id].join('\t'));
  if (!Array.isArray(data.pricing.profiles)) throw new Error();
  if (data.pricing.profiles.includes(process.argv[3])) {
    if (!/^[a-z0-9-]+$/.test(data.pricing.name) || !/^[a-z0-9-]+@\d+\.\d+\.\d+$/.test(data.pricing.package)) throw new Error();
    console.log(['C', data.pricing.name, data.pricing.package].join('\t'));
  }
} catch {
  console.error('Cannot read profiles.json. Download a fresh release and try again.');
  process.exit(1);
}
NODE
  ) || return 1
  MARKET_NAMES=()
  MARKET_SOURCES=()
  PLUGINS=()
  PRICING_NAME=
  PRICING_PKG=
  while IFS=$'\t' read -r kind first second; do
    case "$kind" in
      M) MARKET_NAMES+=("$first"); MARKET_SOURCES+=("$second") ;;
      P) PLUGINS+=("$first") ;;
      C) PRICING_NAME=$first; PRICING_PKG=$second ;;
    esac
  done <<< "$manifest"
}

make_neutral_directory() {
  # Check every candidate's ancestors. A custom TMPDIR may point into a project.
  # Commands run outside projects so a local .mcp.json cannot mask the user entry.
  NEUTRAL_DIR=$(node - "$SETUP_ROOT" <<'NODE'
const fs = require('fs');
const os = require('os');
const path = require('path');
const repo = fs.realpathSync(process.argv[2]);
const candidates = process.platform === 'win32'
  ? [os.tmpdir(), path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local'), 'Temp'), path.join(process.env.SystemRoot || 'C:\\Windows', 'Temp')]
  : [os.tmpdir(), '/private/tmp', '/tmp'];
for (const candidate of candidates) {
  try {
    const base = fs.realpathSync(candidate);
    let safe = true;
    for (let current = base;; current = path.dirname(current)) {
      if (current === repo || fs.existsSync(path.join(current, '.mcp.json')) || fs.existsSync(path.join(current, '.git'))) { safe = false; break; }
      if (path.dirname(current) === current) break;
    }
    if (!safe) continue;
    const created = fs.mkdtempSync(path.join(base, 'claude-launchpad-'));
    console.log(process.platform === 'win32' ? created.replace(/\\/g, '/') : created);
    process.exit(0);
  } catch { /* Try the next OS temporary directory. */ }
}
console.error('Cannot create a temporary folder outside a project. Check your OS temporary-folder permissions and try again.');
process.exit(1);
NODE
  ) || return 1
}
