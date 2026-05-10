---
name: youtube-thumbnail
description: Generate YouTube thumbnail options from high-performing YouTube style references, a target person's images, and optional relevant logos/assets. Uses the local youtube-researcher SerpApi workflow to find/pull YouTube thumbnails, internet-image-puller to gather logos/images when needed, and OpenAI image generation/editing to create final 16:9 thumbnails. Defaults to 5 options when the user does not specify a count.
---

# YouTube Thumbnail

Use this skill when Riley asks to make YouTube thumbnails, clone the style of thumbnails that performed well, pull recent thumbnails from a creator/channel, or generate multiple thumbnail options from a face/person reference.

## Default Behavior

- Generate `5` options unless the user gives a different count.
- Use `gpt-image-2` unless the user asks for another image model.
- Use 16:9 output.
- Use one style/reference thumbnail plus up to three target-person images per generation by default.
- Use `youtube-researcher` for YouTube search/channel thumbnail pulls.
- Use `internet-image-puller` when relevant logos, product images, UI screenshots, or supporting graphics are needed.
- Save outputs in a local folder and report exact paths.

## Credentials

Do not write API keys into this skill file.

The helper reads SerpApi in this order:

1. `SERP_API_KEY`
2. `SERPAPI_API_KEY`
3. macOS Keychain item `codex-serpapi-key` for account `rileybrown`

OpenAI image generation reads `OPENAI_API_KEY`.

## Quick Start

Generate five thumbnail options from a channel's latest thumbnails:

```bash
python3 /Users/rileybrown/.codex/skills/youtube-thumbnail/scripts/youtube_thumbnail.py \
  --topic "Riley's latest video: My AI Setup, the AI tools I would install on a brand new computer" \
  --style-channel "https://www.youtube.com/@GregIsenberg" \
  --person-image /Users/rileybrown/Remotion/Riley/riley-04.png \
  --person-image /Users/rileybrown/Remotion/Riley/riley-03.png \
  --person-image /Users/rileybrown/Remotion/Riley/riley-02.png \
  --logo-query "Wispr Flow logo" \
  --logo-query "Raycast app logo" \
  --logo-query "OpenAI Codex logo" \
  --logo-query "Claude Code logo" \
  --output-dir /Users/rileybrown/Remotion/Riley/youtube-thumbnail-run
```

Generate a specific number:

```bash
python3 /Users/rileybrown/.codex/skills/youtube-thumbnail/scripts/youtube_thumbnail.py \
  --topic "AI tools setup video" \
  --style-channel "@GregIsenberg" \
  --person-image /path/to/person-1.png \
  --person-image /path/to/person-2.png \
  --person-image /path/to/person-3.png \
  --options 3 \
  --output-dir /tmp/thumbs
```

## Workflow

1. Identify the video topic, target person images, and style source.
2. Pull style thumbnails:
   - Prefer `--style-channel` for "latest videos from this creator".
   - Use `--style-query` for topic/search-based examples.
   - The helper saves references under `style-references/`.
3. Pull supporting assets only when helpful:
   - Use `--logo-query` for named tools, products, or brands.
   - The helper saves assets under `pulled-assets/`.
4. Generate thumbnails:
   - Each option uses one style thumbnail and up to three person images.
   - If logos/assets exist, the prompt tells the image model to include the relevant tools/graphics; the helper keeps the core image inputs focused on style + face references.
5. Verify:
   - Confirm final images exist.
   - Confirm dimensions are 16:9.
   - Show or report the final output paths.

## Notes

- If a user says "use the latest videos", use channel mode and report concrete dates/titles.
- If the user gives placeholders like "change text to ____", infer the thumbnail text from the target video topic when obvious; ask only if it is genuinely ambiguous.
- If `gpt-image-2` rejects a parameter, remove that parameter and retry with the same model before switching models.
- Keep the prompt simple and close to Riley's wording: style reference, target face refs, requested text, requested graphic.
