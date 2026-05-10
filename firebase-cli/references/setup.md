# Firebase CLI Setup

Use this file when the wrapper script fails or when the user asks to install or repair the Firebase CLI.

## Preferred Invocation

Run Firebase commands through:

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh ...
```

The wrapper prefers a working standalone binary and avoids broken `firebase` executables on `PATH`.

## Official Install Options

Firebase documents three relevant install paths:

- Auto install script:

```bash
curl -sL https://firebase.tools | bash
```

- Standalone binary: download the platform-specific Firebase CLI binary from `firebase.tools` and add it to `PATH`.
- npm install:

```bash
npm install -g firebase-tools
```

Firebase's CLI docs state that the CLI requires Node.js `v18.0.0` or later.

## Local Environment Note

In the current environment where this skill was created, the globally installed npm-based CLI at `/usr/local/bin/firebase` crashes immediately under `node v25.1.0`. Treat that as a machine-specific compatibility problem, not a guaranteed Firebase limitation. If you see the same failure, use the standalone install path or run the npm-based CLI under an LTS Node version.

## Authentication Priority

The upstream `firebase-tools` README lists these auth methods in descending priority:

1. User token via `--token` or `FIREBASE_TOKEN`
2. Local login via `firebase login`
3. Service account via `GOOGLE_APPLICATION_CREDENTIALS`
4. Application Default Credentials from `gcloud`

For new work:

- Prefer `firebase login` for interactive use.
- Prefer `GOOGLE_APPLICATION_CREDENTIALS=/abs/path/key.json` for automation or CI.
- Avoid `FIREBASE_TOKEN` unless the user explicitly requests it, because the upstream README marks it as deprecated.

## Basic Smoke Test

```bash
/Users/rileybrown/.codex/skills/firebase-cli/scripts/firebase_exec.sh projects:list
```

If that works, the CLI is usable.
