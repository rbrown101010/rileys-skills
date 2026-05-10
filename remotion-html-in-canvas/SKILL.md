---
name: remotion-html-in-canvas
description: Use when creating or modifying Remotion videos that need HTML-in-canvas effects, the HtmlInCanvas component, Canvas 2D/WebGL/WebGPU post-processing, custom HTML-in-canvas transitions, or @remotion/web-renderer HTML-in-canvas rendering.
metadata:
  short-description: Remotion HTML-in-canvas effects
---

# Remotion HTML-in-canvas

Use this skill when a Remotion composition should draw live React/HTML into a canvas for post-processing effects such as blur, distortion, magnification, vintage screen treatment, glitch, WebGL shaders, WebGPU shaders, or custom transition blending.

## Current support

- Requires Remotion `4.0.455` or newer for `<HtmlInCanvas>`.
- The latest checked release was `4.0.457` on May 4, 2026.
- Previewing in Studio requires Chrome Canary 149+ with `chrome://flags/#canvas-draw-element` enabled.
- Rendering via Remotion CLI, Studio, Lambda, Vercel, and server-side rendering works from Remotion `4.0.455`; Remotion ships a compatible Canary build and enables the flag for rendering.
- If WebGL is used, render with `--gl=angle` or set `Config.setChromiumOpenGlRenderer('angle')` in `remotion.config.ts`.
- If no GPU is available, use `--gl=swangle`.

## Core pattern

```tsx
import React, {useCallback} from 'react';
import {
  AbsoluteFill,
  HtmlInCanvas,
  type HtmlInCanvasOnPaint,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const CanvasBlur: React.FC = () => {
  const frame = useCurrentFrame();
  const {width, height, fps} = useVideoConfig();

  const onPaint: HtmlInCanvasOnPaint = useCallback(
    ({canvas, element, elementImage}) => {
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        throw new Error('Failed to acquire 2D context');
      }

      const t = (frame / fps) * Math.PI * 2;
      ctx.reset();
      ctx.filter = `blur(${8 + Math.sin(t) * 4}px)`;
      const transform = ctx.drawElementImage(elementImage, 0, 0);
      element.style.transform = transform.toString();
    },
    [frame, fps],
  );

  return (
    <HtmlInCanvas width={width} height={height} onPaint={onPaint}>
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          fontSize: 120,
          backgroundColor: '#111',
          color: 'white',
        }}
      >
        Hello
      </AbsoluteFill>
    </HtmlInCanvas>
  );
};
```

## Rules

- Import `HtmlInCanvas`, `HtmlInCanvasOnPaint`, and `HtmlInCanvasOnInit` from `remotion`.
- Use `onPaint` for every-frame drawing and post-processing.
- Use `onInit` for WebGL/WebGPU setup; return a cleanup function.
- Do not nest `<HtmlInCanvas>` inside another `<HtmlInCanvas>`. Merge effects into one `onPaint` callback instead.
- For 2D effects, call `ctx.reset()` before painting, set filters/transforms, then call `ctx.drawElementImage(elementImage, 0, 0)`.
- Assign the returned transform to `element.style.transform`.
- For WebGL, create GPU state in `onInit`, upload the current `elementImage` in `onPaint`, and render the quad/shader there.
- If the project uses the `@remotion/web-renderer` HTML-in-canvas option for client-side full-frame capture, do not place `<HtmlInCanvas>` inside that composition; Chrome cannot nest captures.

## References

- Official overview: https://www.remotion.dev/docs/html-in-canvas
- Component API: https://www.remotion.dev/docs/remotion/html-in-canvas
- Example components: https://github.com/remotion-dev/html-in-canvas
