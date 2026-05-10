---
name: internet-image-puller
description: Use when Codex needs to find images on the public internet and save them into a local directory, especially for brand assets, moodboards, research boards, reference pulls, or site-specific image collection. Supports SerpAPI Google Images search for query-driven discovery and Firecrawl scrape/map workflows for extracting images from specific pages or whole sites.
---

# Internet Image Puller

Use this skill to pull internet images into a local folder without hand-copying URLs.

## Setup

Do not store keys in the skill files. Provide them as environment variables in the shell session:

```bash
export SERP_API_KEY="..."
export FIRECRAWL_API_KEY="..."
```

Check configuration:

```bash
/Users/rileybrown/.codex/skills/internet-image-puller/scripts/image_puller.py config:show
```

## Command Choice

- Use `serp:search` when the user starts with a query like "find OpenAI logos" or "pull studio photos of waterfalls".
- Use `firecrawl:scrape` when the user gives one page and wants the images from that page.
- Use `firecrawl:site` when the user gives a site and wants images from multiple related pages on that site.

## Quick Start

Search Google Images and download the first 20 results:

```bash
/Users/rileybrown/.codex/skills/internet-image-puller/scripts/image_puller.py serp:search \
  --query "OpenAI logo" \
  --output-dir /tmp/openai-images \
  --limit 20
```

Scrape images from a single page:

```bash
/Users/rileybrown/.codex/skills/internet-image-puller/scripts/image_puller.py firecrawl:scrape \
  --url "https://openai.com/brand/" \
  --output-dir /tmp/openai-brand-assets \
  --limit 100
```

Map a site, filter to relevant pages, then scrape and download images:

```bash
/Users/rileybrown/.codex/skills/internet-image-puller/scripts/image_puller.py firecrawl:site \
  --url "https://openai.com" \
  --map-search "brand codex" \
  --include "/brand" \
  --include "/codex" \
  --output-dir /tmp/openai-codex-assets \
  --page-limit 8 \
  --images-per-page 100
```

## Output Behavior

- Downloads land in the requested output directory.
- The script writes `manifest.json` beside the files and appends future runs in the same folder.
- Filenames are sanitized and deduplicated.
- The downloader strips common CDN resize parameters by default so it can pull the higher-fidelity source file when possible.

## Notes

- Prefer official domains when the user asks for brand assets or logos.
- For search-driven pulls, use `--require-domain openai.com` or another domain filter when the user wants only official sources.
- Firecrawl site extraction can return many images from one page. Start with smaller limits unless the user clearly wants everything.
- If a site blocks direct fetching but Firecrawl can still list the image URLs, keep the failures in the manifest and report the gap.

For endpoint details and caveats, read [references/api-notes.md](./references/api-notes.md).
