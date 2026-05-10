---
name: remodex
description: Connect Codex to the Remodex iPhone app. Use when the user wants to access Codex from their phone, pair or re-pair Remodex, bring the bridge up on macOS, inspect bridge status, reset pairing, resume the last mobile thread on desktop, or manage the local Remodex bridge lifecycle.
---

# Remodex

Pair Codex with the Remodex iPhone app and manage the local bridge from macOS.

## Use This Skill For

- First-time phone pairing
- Re-pairing after a code expires or device state is stale
- Checking whether the bridge is up
- Starting or restarting the background bridge
- Resuming the last active Remodex thread back into Codex on desktop

## Critical Rules

1. Run `remodex` commands in the terminal. Do not invent pairing codes or statuses.
2. Use a TTY for `remodex up` because it prints an ASCII QR and pairing code.
3. If pairing fails or the code expires, rerun `remodex up` instead of trying to reuse an old code.
4. If the user asks where the QR code is, tell them it appears in the terminal output from `remodex up`.

## First-Time Pairing

1. Ensure the required CLIs are installed:

```bash
npm install -g @openai/codex@latest
npm install -g remodex@latest
```

2. Start pairing:

```bash
remodex up
```

3. Tell the user to:
- Scan the ASCII QR from the terminal with the Remodex iPhone app, or
- Paste the pairing code manually in the app

4. Pairing output includes:
- QR code
- pairing code
- session ID
- device ID
- expiration time

## Normal Operations

- Start the bridge and print a fresh QR/code: `remodex up`
- Start background service: `remodex start`
- Restart background service: `remodex restart`
- Stop background service: `remodex stop`
- Check service status: `remodex status`
- Reset device pairing state: `remodex reset-pairing`
- Resume the last active mobile thread in Codex desktop: `remodex resume`
- Watch a thread rollout: `remodex watch [threadId]`

Append `--json` to `start`, `restart`, `stop`, `status`, `reset-pairing`, or `resume` when machine-readable output is useful.

## Troubleshooting

- If the user cannot find the QR code:
  Run `remodex up` again in Terminal and have them scan that terminal output.
- If the pairing code expired:
  Run `remodex up` again to generate a fresh session.
- If the bridge seems stuck:
  Run `remodex status`, then `remodex restart`.
- If the phone and desktop appear out of sync:
  Run `remodex reset-pairing`, then `remodex up`.
- If you need exact command/state details:
  Read [references/cli-and-state.md](references/cli-and-state.md).

