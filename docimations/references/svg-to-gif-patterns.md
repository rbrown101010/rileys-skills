# SVG-to-GIF Patterns

## Use This Pipeline

1. Generate one SVG per animation frame.
2. Convert each SVG to PNG with `sips -s format png frame.svg --out frame.png`.
3. Stitch PNGs into a GIF with Pillow.
4. Keep `svg_frames/` beside the GIF output for later edits.

This is more reliable for Google Docs than embedding animated SVG. Docs accepts GIFs as document images, while SVG animation support is not the target surface.

## Layout Grammar

- Canvas: 1280 x 720.
- Title: x 170, y around 145, 44 px bold.
- Subtitle: x 170, y around 220, 28 px regular.
- Diagram area: y 320-610.
- Box radius: 16-18 px.
- Stroke: 3 px.
- Arrow stroke: 3 px, neutral gray.
- Max nodes per chart: 5 unless the chart is a timeline.

## Animation Grammar

- Boxes: opacity 0 to 1, scale 0.86 to 1.0.
- Arrows: draw by interpolating line end points.
- Branches: draw trunk first, then branch arrows, then destination boxes.
- Timelines: draw rail first, then dots and cards.
- Stacks: reveal bottom-to-top or context-to-memory depending on the story.

## External References

- MDN SVG SMIL guide: https://developer.mozilla.org/docs/Web/SVG/Guides/SVG_animation_with_SMIL
- SVG WG animation spec: https://svgwg.org/specs/animations/
- CSS-Tricks SVG line animation: https://css-tricks.com/svg-line-animation-works/
- CSS-Tricks stroke-dash pattern: https://css-tricks.com/a-trick-that-makes-drawing-svg-lines-way-easier/
- svg-precision skill listing: https://mcp.directory/skills/svg-precision
- drawio-skill repo: https://github.com/Agents365-ai/drawio-skill

For Google Docs output, use those references for SVG thinking, not as a reason to ship animated SVG directly.
