# Realtime Database CLI Notes

Use this file when the user wants to inspect, query, or mutate Firebase Realtime Database data directly from the CLI.

## Instance Management

```bash
firebase database:instances:list
firebase database:instances:create INSTANCE_NAME --location LOCATION
```

From the installed `firebase-tools` command definitions:

- `database:instances:create <instanceName>`
- `--location` is optional and defaults to `us-central1`

## Querying Data

Use `database:get <path>`. The path must start with `/`.

Supported flags from the installed Firebase CLI command definition:

```bash
firebase database:get /PATH
firebase database:get /PATH --pretty
firebase database:get /PATH --shallow
firebase database:get /PATH --export
firebase database:get /PATH --order-by CHILD_KEY
firebase database:get /PATH --order-by-key
firebase database:get /PATH --order-by-value
firebase database:get /PATH --limit-to-first NUM
firebase database:get /PATH --limit-to-last NUM
firebase database:get /PATH --start-at VALUE
firebase database:get /PATH --end-at VALUE
firebase database:get /PATH --equal-to VALUE
firebase database:get /PATH --instance INSTANCE_NAME
```

Example:

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID database:get /messages \
  --order-by timestamp \
  --start-at 1700000000 \
  --limit-to-last 20 \
  --pretty
```

The CLI serializes query values for you, so plain strings, numbers, and booleans are acceptable inputs for most filters.

## Mutating Data

```bash
firebase database:set /PATH VALUE_OR_FILE
firebase database:update /PATH JSON_OBJECT_OR_FILE
firebase database:push /PATH VALUE_OR_FILE
firebase database:remove /PATH
```

Use Realtime Database when the user explicitly wants CLI-readable JSON queries. If they actually need Cloud Firestore data queries, switch to SDKs or other APIs because the Firebase CLI does not expose the same kind of Firestore document query surface.
