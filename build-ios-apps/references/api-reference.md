# Signing Service API Reference

Base URL: `${SIGNING_SERVICE_URL}` (defaults to `https://ios-service.vibecodeapp.com`)

All `/api/*` requests require authentication via the `Authorization` header:

```
Authorization: Bearer $VIBECODE_API_KEY
```

All requests/responses are `Content-Type: application/json`.
Errors: `{"error": "message"}` with appropriate HTTP status.

Public routes (no auth needed): `/health`, `/install/*`, `/register/*`, `/manifest/*`, `/ipa/*`.

---

## Apple Authentication

Two methods for authenticating with Apple. **Auth is one-time only** — once a `userId` is authenticated, it persists across all future signing requests. You never need to re-authenticate the same userId. Signing assets (certs, keys, profiles) are cached per user and reused automatically.

Check if a userId is already saved: `cat ./user-id.txt` (relative to the skill directory).
If it exists, skip auth entirely and go straight to `/api/sign`.

### Method 1: API Key (recommended for automation)

No 2FA, no polling. Ready immediately.

```
POST /api/auth/apikey
```

```json
{
  "userId": "my-user",
  "issuerID": "0940870d-61c8-44b1-a646-5a24bf17d012",
  "keyID": "XP2T5GJP75",
  "p8Key": "-----BEGIN PRIVATE KEY-----\nMIGT...pUJn\n-----END PRIVATE KEY-----",
  "teamId": "8V56LM5E58"
}
```

- `userId` — optional, auto-generated UUID if omitted
- `issuerID` — from App Store Connect > Users and Access > Integrations > Keys
- `keyID` — the key identifier (matches the filename `AuthKey_{keyID}.p8`)
- `p8Key` — full `.p8` file contents including BEGIN/END headers
- `teamId` — Apple Developer team ID

**Response:** `{"ok": true, "userId": "my-user"}`

**IMPORTANT:** The `keyID` must match the actual key, not something else. The `.p8` filename convention is `AuthKey_{keyID}.p8` — use the ID from the filename.

### Method 2: Apple ID + Password (interactive)

Requires polling and 2FA. Better for one-time setup.

**Step 1 — Start auth:**

```
POST /api/auth/start
{"username": "user@example.com", "password": "secret", "userId": "my-user"}
```

Response: `{"sessionId": "...", "userId": "my-user"}`

**Step 2 — Poll status:**

```
GET /api/auth/status/{sessionId}
```

Response includes `state`, `output`, and `teams` (when applicable).

States: `authenticating` → `awaiting_2fa` → `authenticating` → `awaiting_team` → `authenticated`

**Step 3 — Respond to prompts:**

```
POST /api/auth/respond
{"sessionId": "...", "value": "123456"}  // 2FA code
{"sessionId": "...", "value": "1"}       // team selection (1-based index or teamId)
```

Poll `/api/auth/status/{sessionId}` after each respond to see updated state.

SRP session is persisted — subsequent signs auto-refresh the token (~1 year validity, no re-login needed).

---

## Building

### POST /api/build

Upload a source zip to build an unsigned iOS app on a cloud macOS build server.

**Request**: Send the zip as either:
- `multipart/form-data` with a `file` field
- Raw body with `Content-Type: application/zip`

```bash
# multipart (recommended)
curl -X POST ${SIGNING_SERVICE_URL:-https://ios-service.vibecodeapp.com}/api/build \
  -H "Authorization: Bearer $VIBECODE_API_KEY" \
  -F "file=@source.zip"

# raw body
curl -X POST ${SIGNING_SERVICE_URL:-https://ios-service.vibecodeapp.com}/api/build \
  -H "Authorization: Bearer $VIBECODE_API_KEY" \
  -H "Content-Type: application/zip" --data-binary @source.zip
```

Zip must contain a `.xcodeproj` within 3 levels. Max 500 MB. A single top-level wrapper directory is fine.

**Response:**
```json
{"buildJobId": "uuid", "statusUrl": "https://ios-service.vibecodeapp.com/api/build-jobs/uuid"}
```

### GET /api/build-jobs/{jobId}

Poll build status. Typical build time: 2-5 minutes.

```json
{
  "id": "uuid",
  "state": "built",
  "error": null,
  "appUrl": "https://iosbuilds.composerapi.com/raw-builds/uuid.tar.gz",
  "createdAt": 1710900000
}
```

States: `uploading` → `building` → `built` | `failed`

When `state: "built"`, pass `appUrl` to `POST /api/sign`.

### GET /api/build-jobs/{jobId}/logs

Fetch pipeline logs from Azure DevOps. Use this when a build fails to understand why.

```json
{
  "logs": [
    {"id": 1, "lineCount": 42, "text": "Starting: Initialize job\n..."},
    {"id": 2, "lineCount": 15, "text": "Starting: Checkout\n..."}
  ]
}
```

Returns one entry per pipeline task/step. Only available after the Azure pipeline run has started (state must be past `uploading`).

**Errors:** `404` if job not found, `400` if pipeline hasn't started yet, `500` if Azure API fails.

---

## Signing

### POST /api/sign

Starts async signing. Returns immediately — poll build status.

```json
{
  "userId": "my-user",
  "appUrl": "https://iosbuilds.composerapi.com/raw-builds/{buildId}.tar.gz",
  "projectId": "optional-tracking-id"
}
```

- `appUrl` — URL to a `.tar.gz` containing a `.app` bundle (max 500 MB). Must point to an allowed host (`iosbuilds.composerapi.com` or `localhost`).
- Archive format: `MyApp.app/` at root or inside `Payload/` directory

**Response:**

```json
{
  "buildId": "uuid",
  "installUrl": "https://ios-service.vibecodeapp.com/install/{buildId}",
  "statusUrl": "https://ios-service.vibecodeapp.com/api/builds/{buildId}"
}
```

### GET /api/builds/{buildId}

Poll until `state` is `signed` or `failed`. Recommended interval: 2-3 seconds.

```json
{
  "id": "uuid",
  "state": "signed",
  "bundle_id": "com.example.app",
  "bundle_name": "MyApp",
  "error": null,
  "installUrl": "https://ios-service.vibecodeapp.com/install/{buildId}"
}
```

States: `pending` → `signing` → `signed` | `failed`

When `state: "failed"`, check `error` for the reason.

---

## OTA Installation

### GET /install/{buildId}

HTML page with an `itms-services://` link. Open on iPhone to install.
Only works when build `state: "signed"`.

You can also build a custom installation page and link to the build. You can host the custom installation page on [https://chorus.host](https://chorus.host) pretty easily.

### GET /manifest/{buildId}.plist

OTA manifest XML. Called internally by iOS — not for direct use.

### GET /ipa/{buildId}.ipa

Download the signed IPA binary directly.

---

## Errors


| Status | Error                                            | Cause                                  |
| ------ | ------------------------------------------------ | -------------------------------------- |
| 401    | `Missing Authorization header`                   | No Bearer token provided               |
| 401    | `Invalid API key format`                         | Token doesn't start with `vibecode_`   |
| 401    | `Invalid API key`                                | API key not found in database          |
| 400    | `userId and appUrl required`                     | Missing fields on /api/sign            |
| 400    | `appUrl must use http or https`                  | Non-HTTP protocol                      |
| 400    | `appUrl must point to an allowed host`           | Hostname not in allowlist              |
| 400    | `No team selected — authenticate first`          | User not fully authenticated           |
| 400    | `username and password required`                 | Missing credentials on /api/auth/start |
| 400    | `Invalid API key material: ...`                  | Bad .p8 key on /api/auth/apikey        |
| 403    | `userId already belongs to a different Apple ID` | userId conflict                        |
| 404    | `User not found — authenticate first`            | Unknown userId                         |
| 404    | `Session not found`                              | Invalid/expired sessionId              |
| 404    | `Build not found`                                | Invalid buildId                        |


### Async build errors (in `error` field when `state: "failed"`)


| Error                                                       | Cause                                |
| ----------------------------------------------------------- | ------------------------------------ |
| `No .app found in archive`                                  | tar.gz doesn't contain a .app bundle |
| `curl failed (code N): ...`                                 | Failed to download appUrl            |
| `No registered iOS devices were found in App Store Connect` | No devices for provisioning profile  |
| `App Store Connect request failed (409): ...`               | Certificate conflict (existing cert) |
| `zsign failed (code N): ...`                                | Code signing failed                  |


