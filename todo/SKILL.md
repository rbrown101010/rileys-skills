---
name: todo
description: Use when the user says /todo, asks to update the shared todo list, or wants any project to track current work in Riley's shared todo document.
---

# Todo

Point todo updates to this document:

`/Users/rileybrown/Documents/Codex/2026-05-09/please-make-a-markdown-file-that/Todo list.md`

Use the emoji itself as the bullet:

- 🔵 Not done
- 🟢 Done
- 🩶 Backlog / do later

When updating the document, keep it simple. Do not add a status key, markdown bullets, checkboxes, or `[x]` marks. Add current project tasks under `Not done`, use 🔵 for video ideas too, move completed work to `Done`, and put do-later items in `Backlog`.

## Links

When adding or updating a todo item from an active Codex chat thread, append a clickable thread backlink at the end of that item's line.

Direct `codex://threads/<thread-id>` links are not reliably clickable in Markdown. Use a normal local web link labeled `View Thread` that redirects into the Codex deeplink:

```md
[View Thread](http://127.0.0.1:8796/<thread-id>/)
```

Use the active thread's real thread ID in the URL only. Do not print or append the raw thread ID anywhere in the visible todo text. If the thread ID is not available in the chat context, ask Riley to paste the copied Codex deeplink and extract the ID from `codex://threads/<thread-id>`. Do not invent a thread ID.

For each thread link, create or update this redirect page:

`/Users/rileybrown/Documents/Codex/2026-05-09/please-make-a-markdown-file-that/thread-link-server/<thread-id>/index.html`

The redirect page should immediately send the browser to `codex://threads/<thread-id>` and include a fallback button labeled `View Thread`. Do not display the raw thread ID or the raw `codex://threads/<thread-id>` URL on the page.

If the local thread-link server is not already running, serve the `thread-link-server` folder on `127.0.0.1:8796`. Prefer the existing LaunchAgent if present:

`/Users/rileybrown/Library/LaunchAgents/com.riley.codex-newsletter-thread-link.plist`

When the todo item is about a document or artifact, include the artifact link inline before `View Thread`. This includes Google Docs, Google Drive folders/files, Notion pages, local HTML previews, GitHub PRs/issues, Vercel deployments, or any other source/output link created or used for the task. Do not leave the user hunting for the document later.
