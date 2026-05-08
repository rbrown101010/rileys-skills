---
name: docimations
description: Create animated SVG-to-GIF diagrams for Google Docs and similar document workflows. Use when Codex needs to make animated flowcharts, process charts, timelines, decision trees, context maps, explainer diagrams, or doc-ready GIFs from editable SVG source, especially when the user wants clean slide-like charts embedded in a native Google Doc.
---

# Docimations

## Core Idea

Make doc animations as source SVG frames, then convert those frames to GIFs for Google Docs. Do not rely on animated SVG playback inside Docs. Google Docs gets the GIF. The workspace keeps the SVG frames so the chart is editable and repeatable.

## Workflow

1. Draft the chart story first: title, one short setup line, and 3-5 objects max.
2. Use `scripts/docimation_charts.py` for common chart shapes when speed matters.
3. Keep the visual style simple: white 1280 x 720 canvas, left-aligned title, short subtitle, rounded boxes, thin arrows, restrained colors.
4. Render SVG frames to PNG using `/usr/bin/sips`, then stitch PNGs to GIF with Pillow.
5. Always create a `preview_sheet.png` and inspect it before inserting assets into a doc.
6. For a Google Doc, insert text placeholders first, fetch document indexes, then replace placeholders from bottom to top with `insertInlineImage`.

## Fast Script

Run the bundled generator directly:

```bash
python3 /Users/vibemo/.codex/skills/docimations/scripts/docimation_charts.py \
  --preset sample \
  --out "$PWD/outputs/docimations" \
  --frames 32
```

Use a JSON spec for custom charts:

```bash
python3 /Users/vibemo/.codex/skills/docimations/scripts/docimation_charts.py \
  --spec charts.json \
  --out "$PWD/outputs/docimations"
```

Supported chart `type` values:
- `linear`: left-to-right handoff or trend.
- `loop`: four-step operating loop.
- `branch`: one source branching into multiple paths.
- `stack`: layered context or capability stack.
- `timeline`: scheduled or sequential work.
- `hub`: center concept with surrounding context sources.

Minimal spec:

```json
{
  "charts": [
    {
      "id": "model_handoff",
      "type": "linear",
      "title": "Model handoff",
      "subtitle": "A placeholder flow for turning one prompt into a useful output.",
      "nodes": [
        {"label": "Prompt", "note": "what you want", "tone": "gray"},
        {"label": "Plan", "note": "small path", "tone": "green"},
        {"label": "Tools", "note": "do the work", "tone": "purple"},
        {"label": "Result", "note": "ready to use", "tone": "orange"}
      ]
    }
  ]
}
```

## Google Doc Insertion

When using the Google Drive connector:

1. Create the native Doc with `_create_file`.
2. Insert all text and placeholders with `_batch_update_document`.
3. Call `_get_document_text` to get placeholder indexes.
4. Replace placeholders bottom-to-top with `deleteContentRange` and `insertInlineImage`.
5. Pass local GIF paths in `image_uris` as an array, even if inserting one image.

Use a width near `500 PT` and height near `281 PT` for 16:9 charts inside Docs.

## Style Rules

- Keep labels short enough to fit inside boxes.
- Use concrete labels, not vague category names.
- Animate one idea at a time: reveal box, draw arrow, reveal next box.
- Prefer opacity, scale, and progressive line endpoints over flashy motion.
- Make the final frame readable as a static chart.

Read `references/svg-to-gif-patterns.md` when you need animation patterns, SVG constraints, or external references.
