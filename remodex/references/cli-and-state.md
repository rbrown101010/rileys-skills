# Remodex CLI And State

## CLI Surface

Current CLI usage:

```text
remodex up | remodex run | remodex start | remodex restart | remodex stop | remodex status | remodex reset-pairing | remodex resume | remodex watch [threadId] | remodex --version
```

Machine-readable mode is supported by appending `--json` to:

- `start`
- `restart`
- `stop`
- `status`
- `reset-pairing`
- `resume`

## Key Behaviors

- `remodex up` prints an ASCII QR code and manual pairing code
- `remodex resume` reopens the last remembered mobile thread in Codex desktop
- `remodex watch [threadId]` watches a rollout for a thread

## Local State

Default state directory:

```text
~/.remodex
```

Override with:

```text
REMODEX_DEVICE_STATE_DIR
```

Important files:

- `~/.remodex/last-thread.json`
- `~/.remodex/pairing-session.json`
- `~/.remodex/bridge-status.json`
- `~/.remodex/logs/bridge.stdout.log`
- `~/.remodex/logs/bridge.stderr.log`

## Last Active Thread

The desktop resume flow uses:

```text
~/.remodex/last-thread.json
```

and opens:

```text
codex://threads/<threadId>
```

Default desktop bundle ID used by the helper is:

```text
com.openai.codex
```
