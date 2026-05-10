---
name: build-ios-apps
description: Build, sign, and install iOS apps on real devices using the Vibecode signing service. Use when the user wants to build an iOS app from source, sign an iOS app, install on their iPhone, register a device, set up Apple Developer auth, or work with the iOS build/sign/distribute pipeline. Also triggers for "test on device", "put this on my phone", "ship it to my iPhone", or any request to get a Swift/iOS app running on a real device.
---

# iOS App Build, Sign & Install

Build Swift apps, sign them with Apple credentials, install on iPhones via OTA.

## CRITICAL RULES

1. **NEVER use Xcode, xcodebuild, or xcrun.** You do not have Xcode access. ALL building is done through the cloud build pipeline via `./ios-cli`.
2. **NEVER make raw HTTP/curl calls to the signing service.** Always use `./ios-cli`. It handles authentication, polling, error handling, and output formatting.
3. **Every iOS build request MUST go through this skill.** When a user says "build an app", "test on my phone", "put this on my iPhone", "ship it", or anything about getting an iOS app running — use this skill exclusively.
4. **Before writing any app that uses a capability or extension, READ [references/capabilities.md](references/capabilities.md).** It has per-capability rules for entitlement files, Info.plist keys, runtime code, and manual portal steps. Skipping it causes silent install/runtime failures that waste build cycles. Also read [references/gotchas.md](references/gotchas.md) for Xcode 26 compile fixes.

## Environment

These environment variables are automatically available — `ios-cli` picks them up:

- `VIBECODE_API_KEY` — Authentication (required, auto-detected by CLI)
- `SIGNING_SERVICE_URL` — Service URL (auto-detected, defaults to `https://ios-service.vibecodeapp.com`)
- `VIBECODE_PROJECT_ID` — Project ID
- `VIBECODE_USER_ID` — Default user ID (fallback for --user flag)

## CLI

The `./ios-cli` entrypoint is in this skill directory. Run `./ios-cli --help` for full usage, or `./ios-cli skill` to print this document. A Linux reference binary is preserved as `./ios-cli-linux-x64`, but this Codex setup uses the portable `./ios-cli` wrapper.

### Output Modes

Controlled by `--output` global flag:

- `--output text` (default) — logfmt `key="value"` pairs, one line per result. Designed for grep and cut.
- `--output json` — Single JSON object per invocation. Designed for jq and programmatic parsing.
- `--quiet` — Print only the primary identifier (ID or URL). For scripting and piping.

Long-running commands print bracketed event markers to stderr:
`[building]`, `[signing]`, `[done]`, `[error]`

Errors: `ERROR: message` on stderr (text mode) or `{"error":"message","code":"ERROR_CODE"}` on stdout (JSON mode). Exit code 1.

### Commands

| Command | Description |
|---|---|
| `./ios-cli auth start --username <email> --password <pass>` | Start Apple ID auth (returns sessionId) |
| `./ios-cli auth apikey --user <id> --issuer-id <id> --key-id <id> --p8-key <path> --team-id <id>` | Auth with App Store Connect API key |
| `./ios-cli auth status <sessionId>` | Poll auth session state |
| `./ios-cli auth respond --session <id> --value <code>` | Submit 2FA code or team selection |
| `./ios-cli build <zip-path>` | Upload source zip, build on cloud macOS, wait until done |
| `./ios-cli sign <buildJobId>` | Sign a built app, wait until done, returns install URL |
| `./ios-cli devices [userId]` | List registered devices |
| `./ios-cli register-apple [userId]` | Sync pending devices with Apple |
| `./ios-cli status build <jobId>` | Check build job status |
| `./ios-cli status sign <buildId>` | Check signing status |
| `./ios-cli logs <buildJobId>` | Get Xcode build errors for a failed build |
| `./ios-cli bootstrap <app-name> <bundle-id> <output-dir>` | Create new SwiftUI project from template |
| `./ios-cli config get` | Print current config |
| `./ios-cli config set <key> <value>` | Set a config value (supports dot notation) |
| `./ios-cli config path` | Print config file path |
| `./ios-cli skill` | Print this skill reference |

`[userId]` is optional when `VIBECODE_USER_ID` env var is set.

### Error Codes

If a command fails (exit code 1), check the error code:

| Error Code | Meaning | What To Do |
|---|---|---|
| `MISSING_ENV` | Required env var not set | Ensure `VIBECODE_API_KEY` and `VIBECODE_PROJECT_ID` are available. User can get API key at vibecode.dev/key. |
| `MISSING_ARG` | Required command argument missing | Check command usage with `--help`. |
| `MISSING_FLAG` | Required `--flag` not provided | Check command usage with `--help`. |
| `MISSING_USER_ID` | No `--user` flag and no `VIBECODE_USER_ID` env var | Pass `--user <id>` or set `VIBECODE_USER_ID`. |
| `UNKNOWN_COMMAND` | Unrecognized command or subcommand | Run `./ios-cli --help` to see available commands. |
| `CONNECTION_FAILED` | Cannot reach the signing service | Check `SIGNING_SERVICE_URL`. Service may be down. Retry after a few seconds. |
| `UNAUTHORIZED` | Invalid or expired API key (401) | Check `VIBECODE_API_KEY`. User may need a new key from vibecode.dev/key. |
| `FORBIDDEN` | Access denied (403) | The API key doesn't have permission for this operation. |
| `NOT_FOUND` | Resource not found (404) | The userId, buildJobId, sessionId, or buildId doesn't exist. Verify the ID. |
| `CLIENT_ERROR` | Other client error (4xx) | Check the error message for details. |
| `SERVER_ERROR` | Server error (5xx) | The signing service had an internal error. Retry. If persistent, report the issue. |
| `BUILD_FAILED` | Cloud build failed | Fetch Xcode errors with `./ios-cli logs <jobId>`. Common causes: missing scheme, Swift compiler errors. |
| `BUILD_NOT_READY` | Build hasn't finished yet | Wait for build to complete. Check with `./ios-cli status build <jobId>`. |
| `SIGN_FAILED` | Code signing failed | Usually means no registered devices or expired Apple credentials. Re-authenticate and register devices. |
| `UNEXPECTED_ERROR` | Unknown/unhandled error | Check the error message. May be a bug — retry or report. |

**Auth-specific errors:**
- `auth start` returns `CONNECTION_FAILED` → signing service may be down
- `auth status` returns `state="auth_failed"` → wrong credentials or Apple blocked the login. Try API key auth instead.
- 2FA code rejected → ask user for a fresh code, they expire quickly

### Output Examples

```bash
# Default (logfmt text)
./ios-cli devices c906084e-...
# → devices="0" registrationUrl="https://ios-service.vibecodeapp.com/register/c906084e-..."

# JSON mode
./ios-cli --output json devices c906084e-...
# → {"devices":[],"registrationUrl":"https://..."}

# Quiet mode (just UDIDs)
./ios-cli --quiet devices c906084e-...
# → (one UDID per line)

# Build with progress events on stderr
./ios-cli build /tmp/source.zip
# stderr: [build] uploading /tmp/source.zip...
# stderr: [build] job abc123 started
# stderr: [building] 30s elapsed, state=building
# stderr: [done] build succeeded
# stdout: buildJobId="abc123" state="built" appUrl="https://..."
```

### Chaining Commands

The full build → sign → install flow:

```bash
# 1. Build (outputs buildJobId)
./ios-cli build /tmp/source.zip
# → buildJobId="abc123" state="built" appUrl="https://..."

# 2. Sign using the buildJobId from step 1
./ios-cli sign abc123
# → buildId="def456" state="signed" installUrl="https://ios-service.vibecodeapp.com/install/def456"

# 3. Give the user the installUrl to open on their iPhone
```

With quiet mode for scripting:

```bash
# Build and capture just the job ID
BUILD_JOB_ID=$(./ios-cli --quiet build /tmp/source.zip)

# Sign and capture just the install URL
INSTALL_URL=$(./ios-cli --quiet sign "$BUILD_JOB_ID")

# Share with user
echo "Install your app: $INSTALL_URL"
```

## State

All state lives at `~/.vibecode/ios/config.json`. Schema: [config-schema.json](references/config-schema.json).

!`cat ~/.vibecode/ios/config.json 2>/dev/null || echo "No config found — run first-time setup."`

## Routing

If no config exists or no `activeUser` is set: follow **First-Time Setup** below.
Otherwise: skip to **Normal Flow**.

---

## First-Time Setup

Walk the user through each step. Update `~/.vibecode/ios/config.json` after each one.

### Step 0: Pre-requisites

The user **must** be enrolled in the Apple Developer Program ($99/year). If they are not, they cannot use this skill. Begin by asking them if they are enrolled. If not, guide them on how to enroll.

### Step 1: Authenticate with Apple

Ask for the user's **Apple ID email** and **password**. Explain:
> "Your email and password are sent once to Apple to authenticate. They are not stored — only a session token is saved on the signing service."

Use the password auth flow:

```bash
# Start auth — returns sessionId and userId
./ios-cli --output json auth start --username "user@example.com" --password "their-password"

# Poll until state is "awaiting_2fa"
./ios-cli --output json auth status <sessionId>

# Ask user for the 6-digit code from their Apple device
./ios-cli auth respond --session <sessionId> --value "123456"

# Poll again until state is "awaiting_team"
./ios-cli --output json auth status <sessionId>

# Show team list from the JSON output, ask user to pick (1-based index)
./ios-cli auth respond --session <sessionId> --value "1"
```

If the password flow fails, fall back to **API key auth**:
> "The password login didn't work. You can use an App Store Connect API key instead. Go to App Store Connect > Users and Access > Integrations > Keys to create one."

```bash
./ios-cli auth apikey \
  --user <userId> \
  --issuer-id <issuerID> \
  --key-id <keyID> \
  --p8-key /path/to/AuthKey_XXXX.p8 \
  --team-id <teamId>
```

After auth succeeds, save to config:
```bash
mkdir -p ~/.vibecode/ios
```
Write `config.json` with `activeUser`, `users.{userId}` containing `appleId`, `teamId`, `teamName`.

### Step 2: Register Device

Check if any devices exist:

```bash
./ios-cli --output json devices <userId>
```

If no devices (empty `devices` array in JSON output):
1. Give the user the `registrationUrl` from the JSON output
2. Tell them to open it **on their iPhone** and tap "Register Device"
3. They'll download a profile — guide them: **Settings > General > VPN & Device Management > install the profile**
4. After success page appears, sync with Apple:

```bash
./ios-cli register-apple <userId>
```

Also remind them to **enable Developer Mode**:
> Settings > Privacy & Security > Developer Mode > toggle ON > restart when prompted.

### Step 3: Build, Sign, Install

Follow the **Normal Flow** below.

---

## Normal Flow

### 1. Generate App Icon

Before building, generate an app icon if one doesn't exist at `Assets.xcassets/AppIcon.appiconset/AppIcon.png`. Read the source code you just wrote and identify what makes this app's **value** unique — not its category. Pick the one visual element that would make someone understand what the app does at a glance.

Use Gemini CLI's nanobanana `/icon` command:

```bash
/icon "App icon design for [app description]. [Visual element] with subtle 3D depth. Premium quality, sophisticated, single focal point, subtle lighting" --sizes="1024" --type="app-icon" --style="modern" --corners="sharp"
```

Always include: `Premium quality, sophisticated, single focal point, subtle lighting`. You can add the app's color scheme from the source code if it has one.

**Examples:**
- `/icon "App icon design for streak habit tracker. Minimalist progress rings with subtle 3D depth. Premium quality, sophisticated, single focal point, subtle lighting" --sizes="1024" --type="app-icon" --style="modern" --corners="sharp"`
- `/icon "App icon design for surf forecast app. Ocean wave curling with subtle 3D depth. Premium quality, sophisticated, single focal point, subtle lighting" --sizes="1024" --type="app-icon" --style="modern" --corners="sharp"`
- `/icon "App icon design for split expense tracker. Two overlapping coins with subtle 3D depth. Premium quality, sophisticated, single focal point, subtle lighting" --sizes="1024" --type="app-icon" --style="modern" --corners="sharp"`

Copy the generated PNG into the asset catalog:

```bash
mkdir -p "{project}/Assets.xcassets/AppIcon.appiconset"
cp [generated-icon-path] "{project}/Assets.xcassets/AppIcon.appiconset/AppIcon.png"
cat > "{project}/Assets.xcassets/AppIcon.appiconset/Contents.json" << 'EOF'
{"images":[{"filename":"AppIcon.png","idiom":"universal","platform":"ios","size":"1024x1024"}],"info":{"author":"xcode","version":1}}
EOF
```

### 2. Build

```bash
cd /path/to/project
zip -r /tmp/source.zip . -x ".git/*" -x "xcuserdata/*" -x "*.xcuserstate"
./ios-cli build /tmp/source.zip
```

The CLI uploads, builds on cloud macOS, and waits until complete. Outputs `buildJobId`, `state`, and `appUrl`.

**If the build fails**, fetch the Xcode compilation errors and fix them:

1. Run `./ios-cli logs <buildJobId>` to get the error lines from the build
2. Fix the errors in your source code based on what the compiler says
3. Re-zip and rebuild: `zip -r /tmp/source.zip . -x ".git/*" -x "xcuserdata/*" -x "*.xcuserstate" && ./ios-cli build /tmp/source.zip`

Do NOT give up after a failed build. Read the errors, fix the code, rebuild. Most build failures are missing imports, type mismatches, or project configuration issues that are straightforward to fix from the compiler output.

**Build environment**: The build server uses **Xcode 26.0.1** on macOS. Builds run with `-sdk iphoneos` and `CODE_SIGNING_ALLOWED=NO`. The scheme is auto-detected from the `.xcodeproj` — for multi-target projects (app + widget extension), ensure the main app scheme is listed first.

Save `buildJobId` to config under the active project.

### 3. Sign

```bash
./ios-cli sign <buildJobId>
```

The CLI fetches the build's `appUrl`, signs it, waits until complete, and outputs `buildId`, `installUrl`, `bundleId`, and `bundleName`.

Save `buildId` and `installUrl` to config.

### 4. Install

Give the user the `installUrl` from the sign output — they open it on their iPhone to install.

---

## Re-Sign After New Device

When a new device is registered, the current build needs re-signing (the provisioning profile must include the new device UDID).

Check config for the active project's `buildJobId`. If it exists:
> "New device registered. Re-sign your current build to include it?"

Then re-trigger: `./ios-cli sign <buildJobId>`. No rebuild needed.

---

## Creating a New Project

```bash
./ios-cli bootstrap "My App" "com.example.myapp" /path/to/project
```

Creates a SwiftUI project with SwiftData, tests, asset catalogs from the built-in template. Replaces all placeholders with your app name and bundle ID. Initializes a git repo.

Add new `.swift` files directly into the `{App Name}/` directory — Xcode picks them up automatically.

After bootstrapping, save to config:

```bash
./ios-cli config set activeUser <userId>
./ios-cli config set users.<userId>.teamId <teamId>
```

---

## References

- [API Reference](references/api-reference.md) — all signing service endpoints
- [Capabilities & Entitlements](references/capabilities.md) — per-capability rules, entitlements, Info.plist keys, extension matrix
- [Device Registration](references/device-registration.md) — UDID enrollment flow details
- [Config Schema](references/config-schema.json) — config file structure
- [Gotchas](references/gotchas.md) — common issues and fixes
