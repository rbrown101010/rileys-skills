---
name: youtube-researcher
description: "Use when the user wants YouTube research at speed: finding relevant videos in a niche, scanning channels, pulling transcripts, comparing competitors, or gathering source material from YouTube before summarizing trends, hooks, topics, or positioning. This skill uses a local helper script wired to SerpApi for YouTube search and Supadata for fast transcripts and channel data."
---

# YouTube Researcher

## Overview

Use this skill for YouTube topic research, niche scouting, competitor scans, channel review, and transcript collection. Prefer the bundled script over ad hoc API calls so the workflow stays fast, repeatable, and consistent across chats.

## Quick Start

Run the helper script directly:

```bash
python3 /Users/rileybrown/.codex/skills/youtube-researcher/scripts/youtube_research.py --help
```

Common commands:

```bash
python3 /Users/rileybrown/.codex/skills/youtube-researcher/scripts/youtube_research.py search "ai coding agents" --limit 10 --json

python3 /Users/rileybrown/.codex/skills/youtube-researcher/scripts/youtube_research.py search "b2b saas onboarding" --limit 8 --transcripts 5 --excerpt-chars 900 --json

python3 /Users/rileybrown/.codex/skills/youtube-researcher/scripts/youtube_research.py channel "@ycombinator" --limit 12 --with-transcripts 3 --json

python3 /Users/rileybrown/.codex/skills/youtube-researcher/scripts/youtube_research.py transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --lang en
```

## Workflow

### 1. Search the niche

Start with `search` when the user is exploring a topic, niche, idea cluster, or competitor landscape.

- Use `--limit` to pull more videos.
- Use `--channel "name"` to keep only results whose channel name matches a substring.
- Use `--sp` when the user wants a YouTube-native filter token copied from a filtered YouTube URL.
- Use `--no-cache` for fast-changing topics when freshness matters.

### 2. Pull transcripts only where useful

Transcripts cost more requests than search, so avoid fetching them for everything unless the user clearly needs them.

- Use `--transcripts N` on `search` to fetch transcripts for the top `N` search results.
- Use `transcript` for one-off deep dives.
- Use `--mode native` if the user wants only existing captions and wants to avoid AI-generated fallback.
- Use `--mode auto` for the default fast path.

### 3. Inspect channels directly

Use `channel` when the user wants to understand a creator, competitor, or niche-specific publisher.

- It fetches Supadata channel metadata plus recent video IDs.
- It enriches returned videos with metadata so titles, views, dates, and thumbnails are available without extra work.
- Use `--with-transcripts N` to attach transcript excerpts for the first `N` channel videos.

### 4. Synthesize in-chat

After using the script, do the analysis in the chat:

- recurring hooks or thumbnail/title patterns
- topic clusters and content gaps
- channel positioning
- common claims, framing, and audience promises
- relevant videos worth deeper review

## Output Guidance

- Prefer `--json` when the result will be analyzed further in the chat.
- Prefer plain output when the user mainly wants a quick list or transcript excerpt.
- For “latest” or time-sensitive requests, pair `--no-cache` with concrete dates in the final answer.

## Keys

This skill already has local default API keys wired into the script from the user’s provided credentials. Environment variables override them if needed:

- `SUPADATA_API_KEY`
- `SERPAPI_KEY`

If a key rotates later, update the script or export a new environment variable before running it.

## References

- `references/api-notes.md` for the current endpoint notes and parameter reminders
