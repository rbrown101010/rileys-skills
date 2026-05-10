---
name: video-analysis
description: "Use when the user wants a local video analyzed with the Gemini API, especially for transcript, summary, key visuals, timestamped scene notes, creator/content critique, or fast visual breakdowns from .mp4, .mov, .m4v, or .webm files. The skill uses a bundled helper that chooses inline upload for small videos and Gemini Files API for larger videos."
---

# Video Analysis

## Overview

Use this skill to analyze local video files with Gemini and return a transcript, summary, and key visuals. Prefer the bundled helper over hand-written API calls so upload, polling, prompting, and cleanup stay consistent.

## Quick Start

Run:

```bash
GEMINI_API_KEY="$GEMINI_API_KEY" python3 /Users/rileybrown/.codex/skills/video-analysis/scripts/analyze_video.py /path/to/video.mp4
```

For JSON output:

```bash
GEMINI_API_KEY="$GEMINI_API_KEY" python3 /Users/rileybrown/.codex/skills/video-analysis/scripts/analyze_video.py /path/to/video.mp4 --json
```

Use `--prompt "..."` when the user wants a specific analysis lens.

## Workflow

1. Confirm the file exists and is a video.
2. Use the helper script.
3. Return the useful sections directly in chat unless the user asks for a file.

The helper automatically:

- uses inline Gemini upload for small files
- uses Gemini Files API for larger files
- waits for file processing
- asks for transcript, summary, and key visuals
- deletes the temporary Gemini uploaded file by default

## Secret Handling

Never write the Gemini key into `SKILL.md`, helper scripts, shell profiles, or output files. Use `GEMINI_API_KEY` from the current environment. If the user pastes a key in chat, treat it as temporary for that run only.

## Output Shape

Default to three sections:

- `Transcript`: rough timestamps and spoken words; mark unclear parts as `[unclear]`
- `Summary`: plain-language explanation of the video's main point
- `Key visuals`: timestamped visual notes covering subjects, UI, on-screen text, motion, cuts, framing, and standout moments

For creator workflows, add short extra sections only when useful, such as `Hook`, `Why it works`, `Reusable notes`, or `Shot list`.
