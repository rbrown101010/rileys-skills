---
name: typefully-control
description: >
  Fully control Typefully from Codex. Use this skill when asked to inspect or manage
  Typefully social sets, drafts, tags, queue, analytics, media uploads, or to call
  arbitrary Typefully API endpoints directly.
---

# Typefully Control

Use this skill to control Typefully through its public REST API.

## Version note

As of April 17, 2026, Typefully's publicly documented and live API is `v2`.
Do not assume a public `v3` exists unless `api:probe` or the official docs prove it.

- Docs: `https://typefully.com/docs/api`
- Help overview: `https://support.typefully.com/en/articles/8718287-typefully-api`
- Default public base: `https://api.typefully.com/v2`

## Setup

The CLI is zero-dependency beyond Node.js 18+.

Configure the API key:

```bash
/Users/rileybrown/.codex/skills/typefully-control/scripts/typefully.js setup --key "<TYPEFULLY_API_KEY>" --location global --default-social-set <social_set_id>
```

Check configuration:

```bash
/Users/rileybrown/.codex/skills/typefully-control/scripts/typefully.js config:show
```

## High-signal commands

- `me:get`: authenticated user details
- `social-sets:list`: list accessible Typefully accounts
- `social-sets:get <id>`: inspect one social set and its connected platforms
- `drafts:create ...`: create a draft
- `drafts:update ...`: update a draft
- `drafts:publish ...`: publish immediately
- `drafts:schedule ... --time <iso|next-free-slot>`: schedule a draft
- `tags:list`, `tags:create`: tag management
- `queue:get`, `queue:schedule:get`, `queue:schedule:put`: queue inspection and editing
- `analytics:posts:list`: X post analytics
- `media:upload`, `media:status`: upload assets and poll processing

## Full control

For arbitrary endpoint access, use the raw request command:

```bash
/Users/rileybrown/.codex/skills/typefully-control/scripts/typefully.js api:request GET /v2/social-sets
/Users/rileybrown/.codex/skills/typefully-control/scripts/typefully.js api:request PATCH /v2/social-sets/123/drafts/abc --body '{"publish_at":"now"}'
```

`api:request` accepts:

- versioned paths like `/v2/social-sets`
- relative paths like `/social-sets` or `social-sets` against the configured API base
- full URLs like `https://api.typefully.com/v2/social-sets`

Use `--body '<json>'` or `--body-file <path>` for request payloads.

## Version probe

To verify what Typefully exposes right now:

```bash
/Users/rileybrown/.codex/skills/typefully-control/scripts/typefully.js api:probe
```

## Workflow

1. Run `config:show`.
2. If no default social set is configured, run `social-sets:list` and choose one.
3. Prefer draft creation for tests unless the user explicitly asks to publish live.
4. Use `api:request` when the user needs an endpoint the higher-level commands do not wrap.
