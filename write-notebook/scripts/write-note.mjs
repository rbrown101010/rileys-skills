#!/usr/bin/env node
import { createRequire } from "node:module";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const DEFAULT_APP_DIR =
  "/Users/rileybrown/Documents/Codex/2026-04-29/neon-postgres-plugin-neon-postgres-openai";

function parseArgs(argv) {
  const args = {};

  for (let i = 0; i < argv.length; i += 1) {
    const item = argv[i];

    if (!item.startsWith("--")) {
      continue;
    }

    const key = item.slice(2);
    const next = argv[i + 1];

    if (!next || next.startsWith("--")) {
      args[key] = true;
      continue;
    }

    args[key] = next;
    i += 1;
  }

  return args;
}

function readEnv(appDir) {
  const envPath = path.join(appDir, ".env.local");

  if (!existsSync(envPath)) {
    throw new Error(`Missing .env.local at ${envPath}`);
  }

  return Object.fromEntries(
    readFileSync(envPath, "utf8")
      .split("\n")
      .filter((line) => line.trim() && !line.trim().startsWith("#"))
      .map((line) => {
        const index = line.indexOf("=");
        return [line.slice(0, index), line.slice(index + 1)];
      })
  );
}

function titleFromMarkdown(markdown) {
  const firstLine = markdown
    .split("\n")
    .map((line) => line.replace(/^#+\s*/, "").trim())
    .find(Boolean);

  return (firstLine || "Untitled").slice(0, 80);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const appDir = process.env.NOTEBOOK_APP_DIR || DEFAULT_APP_DIR;
  const env = readEnv(appDir);

  if (!env.DATABASE_URL) {
    throw new Error("DATABASE_URL is missing from .env.local");
  }

  const requireFromApp = createRequire(path.join(appDir, "package.json"));
  const { neon } = requireFromApp("@neondatabase/serverless");
  const sql = neon(env.DATABASE_URL);

  await sql`
    create table if not exists notebook_notes (
      id bigint generated always as identity primary key,
      title text not null,
      markdown text not null,
      created_at timestamptz not null default now(),
      updated_at timestamptz not null default now()
    )
  `;

  if (args.list) {
    const rows = await sql`
      select id, title, updated_at
      from notebook_notes
      order by updated_at desc
      limit 20
    `;
    console.log(JSON.stringify({ notes: rows }, null, 2));
    return;
  }

  if (args.append) {
    if (!args.title) {
      throw new Error("--append requires --title");
    }

    const matches = await sql`
      select id, title, markdown
      from notebook_notes
      where title = ${args.title}
      order by updated_at desc
      limit 1
    `;

    if (!matches[0]) {
      throw new Error(`No note found with title: ${args.title}`);
    }

    const nextMarkdown = `${matches[0].markdown.trimEnd()}\n\n${args.append}`;
    const rows = await sql`
      update notebook_notes
      set markdown = ${nextMarkdown},
          updated_at = now()
      where id = ${matches[0].id}
      returning id, title, updated_at
    `;
    console.log(JSON.stringify({ action: "appended", note: rows[0] }, null, 2));
    return;
  }

  if (args.id) {
    const markdown = String(args.markdown || "");
    const title = args.title || titleFromMarkdown(markdown);
    const rows = await sql`
      update notebook_notes
      set title = ${title},
          markdown = ${markdown},
          updated_at = now()
      where id = ${args.id}
      returning id, title, updated_at
    `;

    if (!rows[0]) {
      throw new Error(`No note found with id: ${args.id}`);
    }

    console.log(JSON.stringify({ action: "updated", note: rows[0] }, null, 2));
    return;
  }

  const markdown = String(args.markdown || "");
  const title = args.title || titleFromMarkdown(markdown);
  const rows = await sql`
    insert into notebook_notes (title, markdown)
    values (${title}, ${markdown})
    returning id, title, updated_at
  `;
  console.log(JSON.stringify({ action: "inserted", note: rows[0] }, null, 2));
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
