---
name: notion-full-control
description: Use when work requires direct, full Notion API access outside the bundled Notion connector, including searching pages and databases, inspecting schemas, querying database rows, creating or updating pages, appending blocks, and sending raw Notion API requests with a locally configured integration token.
---

# Notion Full Control

Use this skill when the built-in Notion connector is unavailable or insufficient and you need direct Notion API access.

This skill provides a local CLI wrapper around the Notion API with:
- secure token lookup from macOS Keychain
- common commands for search, fetch, query, create, update, and append
- a `raw` command for full API coverage

## Credential source

The CLI resolves credentials in this order:
1. `NOTION_API_KEY`
2. macOS Keychain item with service `codex-notion-api-key`

Do not paste the token into working notes or output unless the user explicitly asks.

## Quick start

Use the bundled script:

```bash
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py whoami
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py search --query "Knowledge Base"
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py query <database_id> --page-size 10
```

## Common workflow

1. Search for the target page or database.
2. Retrieve the page or database object to inspect IDs and properties.
3. Query the database to inspect current rows and schema usage.
4. Create or update pages with explicit property payloads.
5. Append child blocks when the page body needs structured content.
6. Use `raw` for any endpoint not covered by a convenience command.

## Commands

### Identify the integration

```bash
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py whoami
```

### Search

```bash
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py search --query "Master Database"
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py search --query "Riley Brown" --filter-object page
```

### Retrieve page, database, or block

```bash
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py get page <page_id>
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py get database <database_id>
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py get block <block_id>
```

### Query a database

```bash
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py query <database_id> --page-size 25
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py query <database_id> --filter-json '{"property":"Name","title":{"contains":"Riley"}}'
```

### Create or update a page

```bash
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py create-page \
  --parent-database-id <database_id> \
  --properties-json '{"Name":{"title":[{"text":{"content":"Short Form Video SOPs"}}]}}'

python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py update-page <page_id> \
  --properties-json '{"Status":{"select":{"name":"Draft"}}}'
```

### Append blocks

```bash
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py append-blocks <block_id> \
  --children-json '[{"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Hello"}}]}}]'
```

### Raw endpoint access

Use this when a convenience command does not exist.

```bash
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py raw POST /databases/<database_id>/query
python3 /Users/rileybrown/.codex/skills/notion-full-control/scripts/notion_api.py raw PATCH /pages/<page_id> --body-json '{"archived":false}'
```

## Guidance

- Prefer inspecting the database schema before writing properties. Notion property payloads are exacting.
- When working in a database, retrieve the database object first and map user-facing property names to the actual property types.
- For page bodies, append blocks after page creation instead of overloading page properties.
- For unsupported operations, use `raw` rather than improvising the HTTP shape.

## Output discipline

- Keep IDs, URLs, and property payloads exact.
- Return concise summaries to the user, but keep raw API results available in the terminal workflow when needed.
- If a request fails, inspect the returned JSON error before retrying.
