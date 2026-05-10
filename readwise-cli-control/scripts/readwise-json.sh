#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v readwise >/dev/null 2>&1; then
  "${SCRIPT_DIR}/setup-readwise-cli.sh" --install-only
fi

if [[ -n "${READWISE_ACCESS_TOKEN:-${ACCESS_TOKEN:-}}" ]]; then
  "${SCRIPT_DIR}/setup-readwise-cli.sh" >/dev/null
fi

exec readwise --json "$@"
