---
name: quiver-svg
description: Generate, inspect, and vectorize SVG assets with the QuiverAI API. Use when Codex needs to create SVG logos, icons, illustrations, diagrams, or other vector graphics from text prompts, convert raster images such as PNG/JPEG/WebP into SVG, list Quiver models, or troubleshoot QuiverAI API requests using QUIVERAI_API_KEY.
---

# Quiver SVG

## Overview

Use QuiverAI to create production-ready SVGs from text prompts or raster images. Prefer the bundled REST helper when you need a repeatable command-line flow; use the Node SDK only inside projects that already use Node and want Quiver as an application dependency.

## Authentication

- Never write API keys into skill files, repo files, shell history examples, or generated artifacts.
- Read the key from `QUIVERAI_API_KEY` first.
- If `QUIVERAI_API_KEY` is not set, the helper reads the key from macOS Keychain service `codex-quiver-ai`.
- Store a pasted key in Keychain only when the user explicitly asks for durable setup.
- Treat generated SVG as code before embedding it in an app: inspect it for unexpected scripts, external references, or oversized markup.

## Quick Start

If the key is not configured yet, store it in macOS Keychain:

```bash
python3 /Users/rileybrown/.codex/skills/quiver-svg/scripts/quiver_svg.py configure-key
```

Then generate:

```bash
python3 /Users/rileybrown/.codex/skills/quiver-svg/scripts/quiver_svg.py generate \
  --prompt "Flat monochrome rocket icon, centered, clean geometry" \
  --out rocket.svg
```

For model discovery:

```bash
python3 /Users/rileybrown/.codex/skills/quiver-svg/scripts/quiver_svg.py models
```

For image vectorization:

```bash
python3 /Users/rileybrown/.codex/skills/quiver-svg/scripts/quiver_svg.py vectorize \
  --image-file input.png \
  --auto-crop \
  --out input-vectorized.svg
```

## Workflow

1. Confirm a key is configured with `key-status` before making API calls when auth is uncertain.
2. Use `models` when the user asks what Quiver can use or when model availability may matter.
3. Use `generate` for prompt-to-SVG tasks. Default to `arrow-1.1`; use `arrow-1.1-max` when the user asks for highest quality or the asset is detail-sensitive.
4. Use `vectorize` for PNG, JPEG, or WebP to SVG. Manually crop tightly first when possible; otherwise pass `--auto-crop`.
5. Save SVG outputs as explicit files in the working directory or user-requested destination.
6. Open or inspect the SVG after generation when quality, safety, or dimensions matter.

## Prompting

Include the subject, style, palette, and composition. Put production constraints in `--instructions`.

Good prompt:

```text
Minimal vector logo mark for a local courier app: folded paper route arrow forming a C, centered, no text, works at 24px.
```

Good instructions:

```text
Use clean editable SVG structure, no raster images, no external URLs, balanced whitespace, two colors maximum.
```

## Helper Script

The bundled script is at `scripts/quiver_svg.py`.

Commands:

- `models`: calls `GET /v1/models`.
- `generate`: calls `POST /v1/svgs/generations`.
- `vectorize`: calls `POST /v1/svgs/vectorizations`.

Common options:

- `--model arrow-1.1` or `--model arrow-1.1-max`
- `--out path.svg` for one output or `--out output-dir` for multiple outputs
- `--raw-response response.json` to keep Quiver response metadata
- `--temperature`, `--top-p`, `--presence-penalty`, and `--max-output-tokens` when sampling control is needed

For text generation, pass `--reference-url` for web-hosted reference images or `--reference-file` for local image references. Arrow 1.1 supports up to 4 references; Arrow 1.1 Max supports up to 16.

## API Notes

Read `references/quiver-api.md` when you need endpoint details, model guidance, error handling, or parameter ranges.
