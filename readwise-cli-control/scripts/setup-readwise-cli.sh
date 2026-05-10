#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly SKILL_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

readonly DEFAULT_READONLY="false"

usage() {
  cat <<'EOF'
Usage:
  READWISE_ACCESS_TOKEN='...' setup-readwise-cli.sh [--readonly true|false]
  setup-readwise-cli.sh --install-only

Options:
  --readonly true|false  Configure Readwise CLI readonly mode. Default: false.
  --install-only         Install the official CLI but do not authenticate.

Notes:
  - Prefer READWISE_ACCESS_TOKEN in the environment instead of putting the token on the command line.
  - This script uses the official Readwise CLI and its documented token auth flow.
EOF
}

install_only="false"
readonly_mode="${DEFAULT_READONLY}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --readonly)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --readonly" >&2
        exit 2
      fi
      readonly_mode="$2"
      shift 2
      ;;
    --install-only)
      install_only="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "${readonly_mode}" != "true" && "${readonly_mode}" != "false" ]]; then
  echo "--readonly must be 'true' or 'false'" >&2
  exit 2
fi

if ! command -v readwise >/dev/null 2>&1; then
  echo "Installing official Readwise CLI..." >&2
  npm install -g @readwise/cli >/dev/null
fi

echo "Readwise CLI version: $(readwise --version)" >&2

if [[ "${install_only}" == "true" ]]; then
  exit 0
fi

token="${READWISE_ACCESS_TOKEN:-${ACCESS_TOKEN:-}}"
if [[ -z "${token}" ]]; then
  echo "READWISE_ACCESS_TOKEN is required for headless auth." >&2
  echo "Get it from https://readwise.io/access_token" >&2
  exit 2
fi

echo "Authenticating Readwise CLI with access token..." >&2
readwise login-with-token "${token}" >/dev/null

echo "Setting readonly mode to ${readonly_mode}..." >&2
readwise config set readonly "${readonly_mode}" >/dev/null

if [[ "${readonly_mode}" == "false" ]]; then
  # The official docs say disabling readonly logs the CLI out and requires re-authentication.
  readwise login-with-token "${token}" >/dev/null
fi

readwise --refresh >/dev/null 2>&1 || true

echo "Readwise CLI is ready." >&2
echo "Skill directory: ${SKILL_DIR}" >&2
