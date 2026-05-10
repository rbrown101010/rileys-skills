# Firestore CLI Notes

Use this file when creating or managing Cloud Firestore databases with the Firebase CLI.

## What the Firebase CLI Can Do

The official Firebase CLI reference includes these Firestore database administration commands:

```bash
firebase firestore:locations
firebase firestore:databases:create DATABASE_ID --location LOCATION
firebase firestore:databases:list
firebase firestore:databases:get DATABASE_ID
firebase firestore:databases:update DATABASE_ID --delete-protection ENABLED|DISABLED --point-in-time-recovery ENABLED|DISABLED
firebase firestore:databases:delete DATABASE_ID
firebase firestore:indexes --database DATABASE_ID
firebase firestore:databases:clone SOURCE_DATABASE DESTINATION_DATABASE --snapshot-time RFC3339_TIMESTAMP
```

The `firestore:databases:create` command creates a database in native mode. The command requires `--location`.

## Safe Create Flow

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID firestore:locations
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh -P PROJECT_ID firestore:databases:create DATABASE_ID \
  --location LOCATION \
  --delete-protection DISABLED \
  --point-in-time-recovery DISABLED
```

Optional flags on create:

- `--delete-protection ENABLED|DISABLED`
- `--point-in-time-recovery ENABLED|DISABLED`
- `-k, --kms-key-name KMS_KEY_NAME` for CMEK-enabled databases

## Important Limitation

The official Firebase CLI reference does not list a general Firestore document read or query command. Do not promise that the Firebase CLI can search Firestore documents directly.

When the user wants to read or search Firestore data:

- Use a Firebase client SDK or Admin SDK in app code
- Use the Firestore REST API
- Use `gcloud` when the task is really a Google Cloud operation rather than a Firebase CLI task

## Follow-up Work After Creation

After creating a new Firestore database:

- Configure rules for that database
- Confirm indexes if the app depends on compound queries
- Register the client app and print SDK config if the app has not yet been linked
