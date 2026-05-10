---
name: mobile-app
description: Build, prototype, deploy, preview, sign, and install mobile apps. Use when the user wants to make a mobile app, React Native app, iOS app, phone UI prototype, iPhone install, or mobile build using Vibecode. Covers Vibecode CLI mobile projects, local mobile design prototypes, and bundled iOS build/sign/install tooling.
---

# Mobile App

Use this skill when the user wants a mobile app made, previewed, deployed, or installed on a phone.

## Pick the Path

Choose the smallest path that matches the request:

- **New hosted mobile app:** use `vibecode-cli` with platform `mobile`. This is the default when the user says "make a mobile app" and wants the app built by a cloud agent.
- **Clickable local mobile UI:** use `$mobile-design` when the user wants design exploration, screen flow, or a browser preview before a real build.
- **Swift/iOS source to iPhone:** use the bundled `./ios-cli` when the user already has Swift/iOS source, asks to build/sign/install on iPhone, asks for Test on device, or needs Apple device registration.

Do not use Xcode, `xcodebuild`, `xcrun`, raw signing-service `curl`, or manual signing calls for the iPhone install flow. Use the bundled `./ios-cli`.

## Auth

Vibecode auth comes from `VIBECODE_API_KEY`. Keep the key out of app repos, skill files, and final replies.

Before using Vibecode commands locally, load the shell profile and verify access:

```bash
source "$HOME/.zshrc" >/dev/null 2>&1 || true
vibecode-cli user
```

If the key is missing or rejected, ask the user for a Vibecode API key from `vibecode.dev/key`. Do not proceed with Vibecode cloud work without a valid key.

## New Hosted Mobile App

Use the current CLI reference when needed:

```bash
vibecode-cli skill
```

Then create a mobile project and run the agent:

```bash
source "$HOME/.zshrc" >/dev/null 2>&1 || true
PROJECT_ID="$(vibecode-cli projects create --quiet mobile "Short app description")"
vibecode-cli yolo "$PROJECT_ID" "Build a mobile app called ... It should ..."
```

Prompt in product language: what the app is, what the user can do, and how it should feel. Do not over-specify frameworks or file paths unless the user gave them.

When `yolo` finishes, share the public URL first, then offer to set a friendlier `vibecode.run` subdomain:

```bash
vibecode-cli deployments subdomain check myapp
vibecode-cli deployments subdomain set "$PROJECT_ID" myapp
```

Only offer a custom domain if the user mentions owning or wanting one.

## Local Mobile Prototype

Use `$mobile-design` for phone-shaped clickable UI work:

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
python3 "$CODEX_HOME/skills/mobile-design/scripts/scaffold_mobile_app.py" \
  --name "My App" \
  --slug my-app \
  --out output/mobile-design

python3 "$CODEX_HOME/skills/mobile-design/scripts/start_mobile_preview.py" \
  output/mobile-design/my-app \
  --open
```

Leave the user with the local preview URL and the prototype folder.

## Swift/iOS Build, Preview, Sign, Install

The bundled helper lives in this skill folder:

```bash
export MOBILE_APP_SKILL="${CODEX_HOME:-$HOME/.codex}/skills/mobile-app"
cd "$MOBILE_APP_SKILL"
./ios-cli --help
```

For new SwiftUI projects, bootstrap from the bundled template:

```bash
./ios-cli bootstrap "App Name" "com.example.appname" "/path/to/output/App Name"
```

Before building an app that uses native capabilities, read:

- `references/capabilities.md`
- `references/gotchas.md`
- `references/device-registration.md`

Normal source build:

```bash
source "$HOME/.zshrc" >/dev/null 2>&1 || true
cd "/path/to/folder-containing-ios-project"
zip -r /tmp/mobile-app-source.zip "Project Folder"
cd "$MOBILE_APP_SKILL"
./ios-cli build /tmp/mobile-app-source.zip
```

If the user asks to install on iPhone, follow the device/auth/sign flow with `./ios-cli devices`, `./ios-cli register-apple`, and `./ios-cli sign <buildJobId>`. Return the install URL clearly.

## Bundled Resources

- `ios-cli`: portable local wrapper for the Vibecode iOS signing service
- `ios-cli-linux-x64`: original downloaded Linux binary kept as a reference artifact
- `scripts/bootstrap.sh`: SwiftUI template bootstrapper
- `template/`: starter SwiftUI Xcode project
- `references/`: signing API, capabilities, device registration, config schema, and gotchas

## Output Expectations

For mobile app builds, end with the public URL, preview URL, install URL, or local preview URL the user can actually open. Also include the project ID or local folder when it is needed for follow-up work.
