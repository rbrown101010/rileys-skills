---
name: firebase-cli
description: "Use when working with Firebase from the terminal: repairing or installing the Firebase CLI, authenticating, selecting projects, creating or managing Cloud Firestore databases, creating or querying Realtime Database instances, registering Firebase apps, or printing SDK config. Prefer this skill when the user asks to add Firebase to an app, create a Firebase database, inspect Firebase project resources, or run Firebase CLI commands safely."
---

# Firebase CLI

## Overview

Use this skill for Firebase setup and operational work done through the Firebase CLI. It is optimized for app bootstrap, Firestore database administration, Realtime Database queries, and safe CLI execution on machines where the global `firebase` command may be broken.

## Required Inputs

Collect or discover these before making changes:

- `project_id`
- database product: `firestore` or `realtime-database`
- region or location
- auth method: interactive login or service account JSON path
- app platform if app registration or SDK config is needed

Do not ask for API keys just to create a database. For CLI authentication, prefer `firebase login` for interactive work or `GOOGLE_APPLICATION_CREDENTIALS=/abs/path/key.json` for automation. Avoid `FIREBASE_TOKEN` unless the user explicitly asks for it; upstream marks user tokens as deprecated.

## Workflow

### 1. Resolve a Working CLI

Always prefer the wrapper script:

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh --help
```

Run all Firebase commands through that wrapper unless the user explicitly wants a raw command. The wrapper checks common install locations, skips broken executables, and gives repair steps if no working CLI is available.

If the wrapper fails, read `references/setup.md` and fix installation before doing any Firebase work.

### 2. Authenticate

- Interactive local machine:

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh login
```

- Remote shell without localhost callback:

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh login --no-localhost
```

- Automation or CI:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/service-account.json
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh projects:list
```

### 3. Select the Project

List projects first, then either pass `-P PROJECT_ID` per command or switch the local directory:

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh projects:list
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh use PROJECT_ID
```

Prefer `-P PROJECT_ID` in automation and scripted flows.

### 4. Choose the Product Flow

#### Cloud Firestore

Use this for Firestore database administration. The Firebase CLI can create, list, inspect, update, clone, and delete databases, and it can list indexes. Read `references/firestore.md` when doing Firestore work.

Common commands:

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID firestore:locations
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID firestore:databases:create DATABASE_ID --location LOCATION
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID firestore:databases:list
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID firestore:databases:get DATABASE_ID
```

Important limitation: the official Firebase CLI reference does not expose a general Firestore document read or query command. Use the Firebase SDK, Admin SDK, REST API, or `gcloud` for Firestore data reads and search-like queries.

After creating a Firestore database, make sure rules and indexes are configured for that database before assuming client access works.

#### Realtime Database

Use this when the user wants direct CLI reads, writes, or query-style inspection of JSON data. Read `references/realtime-database.md` when doing Realtime Database work.

Common commands:

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID database:instances:list
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID database:instances:create INSTANCE_NAME --location LOCATION
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID database:get /PATH
```

`database:get` supports indexed queries. The path must start with `/`.

Example:

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID database:get /messages \
  --order-by timestamp \
  --start-at 1700000000 \
  --limit-to-last 20
```

For writes, use `database:set`, `database:update`, `database:push`, and `database:remove`.

#### App Registration and SDK Config

Use these when the user is wiring Firebase into a web, iOS, or Android app.

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID apps:create WEB "My Web App"
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID apps:create ANDROID "My Android App" --package-name com.example.app
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID apps:create IOS "My iOS App" --bundle-id com.example.app
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID apps:list
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID apps:sdkconfig WEB FIREBASE_APP_ID
```

Use `apps:sdkconfig ... -o FILE` if the user wants the config written to disk.

## References

- `references/setup.md`: install, repair, and auth guidance
- `references/firestore.md`: Firestore database management commands and limits
- `references/realtime-database.md`: Realtime Database query and write commands
