#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

print_failure() {
  local node_version="unavailable"
  local firebase_path="not found"

  if command -v node >/dev/null 2>&1; then
    node_version="$(node -v 2>/dev/null || printf 'unavailable')"
  fi

  if command -v firebase >/dev/null 2>&1; then
    firebase_path="$(command -v firebase)"
  fi

  cat >&2 <<EOF
No working Firebase CLI was found.

Observed on this machine:
- node: ${node_version}
- firebase on PATH: ${firebase_path}

Recommended fixes from official Firebase docs:
1. Install the standalone CLI: curl -sL https://firebase.tools | bash
2. Or download the standalone binary and add it to PATH.
3. If you use npm, Firebase docs require Node.js v18.0.0 or later. If the npm-installed CLI is broken under your current Node runtime, prefer the standalone binary or rerun under an LTS Node version.

Skill references:
- ${SKILL_DIR}/references/setup.md
EOF
  exit 127
}

probe_candidate() {
  if "$@" --help >/dev/null 2>&1; then
    FIREBASE_CMD=("$@")
    return 0
  fi
  return 1
}

declare -a FIREBASE_CMD=()

if [[ -n "${FIREBASE_BIN:-}" ]]; then
  if [[ -x "${FIREBASE_BIN}" ]] && probe_candidate "${FIREBASE_BIN}"; then
    exec "${FIREBASE_CMD[@]}" "$@"
  fi
fi

for candidate in \
  "${HOME}/.local/bin/firebase" \
  "${HOME}/bin/firebase" \
  "${HOME}/.codex/bin/firebase" \
  "/opt/homebrew/bin/firebase" \
  "/usr/local/bin/firebase"
do
  if [[ -x "${candidate}" ]] && probe_candidate "${candidate}"; then
    exec "${FIREBASE_CMD[@]}" "$@"
  fi
done

if command -v firebase >/dev/null 2>&1; then
  resolved_firebase="$(command -v firebase)"
  if probe_candidate "${resolved_firebase}"; then
    exec "${FIREBASE_CMD[@]}" "$@"
  fi
fi

print_failure
