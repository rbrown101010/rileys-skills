---
name: mobile-design
description: Create or refine mobile app UI as a real, clickable local prototype, usually inside an iPhone-scaled frame with reusable tokens, primitives, and screen components. Use when the user wants mobile-first product design, a polished app concept, a browser preview they can click through locally, screen-to-screen flow exploration, or visual iteration on sizing, spacing, typography, and hierarchy for phones.
---

# Mobile Design

Build mobile UI as a local, clickable prototype instead of static mockups. Default to a real phone canvas, a consistent design system, and a browser preview the user can click through immediately.

## Default workflow

1. Create or reuse a workspace folder under `output/mobile-design/<slug>/`.
2. Scaffold the bundled starter when there is no existing prototype.
3. Keep the architecture stable: `styles.css` -> `data.jsx` -> `primitives.jsx` -> `screens.jsx` -> `app.jsx`.
4. Launch a local preview server and open the browser.
5. Iterate in short loops: edit, reload, inspect, refine.

Use these commands:

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export MOBILE_DESIGN_SKILL="$CODEX_HOME/skills/mobile-design"

python3 "$MOBILE_DESIGN_SKILL/scripts/scaffold_mobile_app.py" \
  --name "My App" \
  --slug my-app \
  --out output/mobile-design

python3 "$MOBILE_DESIGN_SKILL/scripts/start_mobile_preview.py" \
  output/mobile-design/my-app \
  --open
```

Stop a running preview with:

```bash
python3 "$MOBILE_DESIGN_SKILL/scripts/stop_mobile_preview.py" \
  output/mobile-design/my-app
```

## Design rules

Work from these defaults unless the user asks for a different visual language:

- Use a fixed internal canvas of `402x874` and scale it with `transform: scale()` to fit the window.
- Respect iOS safe areas. Keep important content clear of the status bar and home indicator.
- Keep tap targets at `44px` minimum. Primary buttons should usually be `52px` to `56px` tall.
- Use a small, disciplined type ramp. Never go below `11px`.
- Keep horizontal padding consistent, usually `20px`.
- Use an `8px` rhythm for spacing.
- Reuse a narrow color vocabulary: background, surface, border, primary text, secondary text, one accent.
- Prefer consistency through tokens and components over screen-by-screen styling.
- Use one accent color sparingly. Primary CTA, selected tab, active chip, and focused state are enough.
- Use small motion only where it clarifies feedback.

For the visual system and consistency model, open only what you need:

- `references/mobile-visual-system.md`
- `references/component-architecture.md`

## File roles

- `styles.css`: global tokens, fonts, backdrop, shared utility classes
- `iOS.jsx`: device shell and iOS chrome
- `data.jsx`: seed content and configuration
- `primitives.jsx`: buttons, chips, cards, avatar marks, icons, tab bar
- `screens.jsx`: screen composition and screen-specific layout
- `app.jsx`: routing, state, mobile scale logic, mounting

Do not collapse everything into one file unless the request is tiny. Keep tokens, primitives, and screens separate so the prototype stays editable.

## Existing apps

When the repo already contains a mobile web app or design sandbox:

- Reuse the existing app and dev server when that is clearly faster.
- Preserve the app's established visual language unless the user asks for a redesign.
- Still apply the same mobile rules: real device canvas, safe areas, touch targets, consistent tokens, reusable primitives.

Use the bundled starter when the user wants a fresh concept, a rapid design exploration, or a standalone prototype.

## Browser validation

This skill should leave the user with something they can click through locally.

- Prefer a real browser preview over screenshots.
- If you need automated browser interaction, screenshots, or UI bug isolation, also use `$playwright`.
- After major layout changes, verify the top safe area, bottom safe area, vertical rhythm, and any long text wrapping.

## Output expectations

By default, produce:

- a local prototype folder in the current workspace
- a running preview URL
- a click-through flow with at least one primary path

If the user only asks for guidance and not implementation, keep the advice tied to this system instead of giving generic mobile design theory.
