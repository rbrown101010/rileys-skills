---
name: buffer-publisher
description: Use Buffer's GraphQL API to inspect Buffer accounts, organizations, channels, queues, posts, daily limits, and to create Buffer Ideas, drafts, scheduled posts, queued posts, or media posts. Use when the user asks to draft, schedule, queue, publish, edit, delete, review, list, or manage social posts through Buffer, or asks what is connected in their Buffer account.
---

# Buffer Publisher

Use this skill to operate Buffer through the GraphQL API. Prefer the bundled helper script for repeatable requests:

```bash
python3 /Users/rileybrown/.codex/skills/buffer-publisher/scripts/buffer_cli.py <command> [options]
```

The helper reads credentials in this order:

1. `BUFFER_API_KEY`
2. macOS Keychain item `codex-buffer-api-key`

Never print, paste, or commit the API key. If authentication fails, ask the user to refresh the Buffer key and store it again.

## Default Workflow

1. Run `account` to confirm access and find organizations.
2. Run `channels --organization-id <id>` to select the target channel.
3. For posts, use `preview-post` first unless the user explicitly asked to create something immediately.
4. For publish-affecting actions, show a concise preflight summary: organization, channel, service, text, assets, mode, and time.
5. Require explicit confirmation before `shareNow`, `customScheduled`, `edit-post`, or `delete-post`.
6. Prefer `create-idea` or `create-post --draft` when the user wants to save content but has not clearly asked to publish or schedule.

## Common Commands

```bash
# Account and orgs
python3 /Users/rileybrown/.codex/skills/buffer-publisher/scripts/buffer_cli.py account

# Channels in an org
python3 /Users/rileybrown/.codex/skills/buffer-publisher/scripts/buffer_cli.py channels --organization-id ORG_ID

# Scheduled posts for one channel
python3 /Users/rileybrown/.codex/skills/buffer-publisher/scripts/buffer_cli.py posts --organization-id ORG_ID --channel-id CHANNEL_ID --status scheduled --limit 20

# Daily posting limits
python3 /Users/rileybrown/.codex/skills/buffer-publisher/scripts/buffer_cli.py daily-limits --channel-id CHANNEL_ID --date 2026-04-22

# Create an idea
python3 /Users/rileybrown/.codex/skills/buffer-publisher/scripts/buffer_cli.py create-idea --organization-id ORG_ID --title "Idea title" --text "Idea body"

# Save a draft post
python3 /Users/rileybrown/.codex/skills/buffer-publisher/scripts/buffer_cli.py create-post --channel-id CHANNEL_ID --text "Post copy" --draft

# Add to queue
python3 /Users/rileybrown/.codex/skills/buffer-publisher/scripts/buffer_cli.py create-post --channel-id CHANNEL_ID --text "Post copy" --mode addToQueue

# Schedule for an exact UTC time
python3 /Users/rileybrown/.codex/skills/buffer-publisher/scripts/buffer_cli.py create-post --channel-id CHANNEL_ID --text "Post copy" --mode customScheduled --due-at 2026-04-24T17:00:00.000Z

# Delete requires an explicit CLI confirmation flag after user confirmation in chat
python3 /Users/rileybrown/.codex/skills/buffer-publisher/scripts/buffer_cli.py delete-post --id POST_ID --yes
```

## Capabilities

- Read account, organization, and channel state.
- List posts with filters for status, channel, date, due date, created date, tags, pagination, and sorting.
- Fetch a single post by ID.
- Check daily posting limits for channels.
- Create Ideas with title, text, services, target date, and media URLs.
- Create text, image, video, document, and link posts from public URLs.
- Save posts as drafts, add to queue, share next, share now, or schedule for a fixed UTC time.
- Edit or delete posts only after explicit user confirmation.

## Safety Rules

- Do not use `shareNow` unless the user explicitly asks to publish immediately.
- Do not use `customScheduled` until the requested local time has been converted to a concrete UTC ISO-8601 `dueAt`.
- Do not delete or edit without repeating the target post ID and receiving confirmation.
- Do not attempt to upload local media files directly; Buffer post assets require reachable URLs.
- Do not post to locked or disconnected channels; pick another channel or ask the user to reconnect it in Buffer.
- Include `MutationError { message }` or equivalent error fragments in mutations.
- Keep queries flat and paginated. Use `first` around 20-50 for list operations.

## References

Read `references/buffer-api.md` when you need endpoint details, allowed enums, supported platforms, rate limits, or GraphQL input shapes.
