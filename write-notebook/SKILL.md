---
name: write-notebook
description: Write directly to Riley's local Neon-backed notebook app. Use when the user asks to save, add, append, update, or inspect notebook notes without using the UI.
---

# Write Notebook

Use this skill to write directly into Riley's single-user notebook app backed by
Neon Postgres.

## Notebook App

Default app directory:

```bash
/Users/rileybrown/Documents/Codex/2026-04-29/neon-postgres-plugin-neon-postgres-openai
```

The skill reads `DATABASE_URL` from that app's `.env.local`. Do not copy the
database URL into skill files or chat output.

## Commands

Add a note:

```bash
node /Users/rileybrown/.codex/skills/write-notebook/scripts/write-note.mjs --title "Title" --markdown "# Title

Markdown body"
```

List recent notes:

```bash
node /Users/rileybrown/.codex/skills/write-notebook/scripts/write-note.mjs --list
```

Update an existing note by id:

```bash
node /Users/rileybrown/.codex/skills/write-notebook/scripts/write-note.mjs --id 1 --markdown "# Updated

New body"
```

Append to an existing note by title:

```bash
node /Users/rileybrown/.codex/skills/write-notebook/scripts/write-note.mjs --title "Daily" --append "New line"
```

## Behavior

- Store notes in `public.notebook_notes`.
- Derive the title from the first non-empty markdown line when `--title` is not
  provided.
- For append, find the newest note with the provided exact title.
- Keep output short: note id, title, and whether the command inserted, updated,
  appended, or listed notes.
- If the app path changes, set `NOTEBOOK_APP_DIR` before running the script.
