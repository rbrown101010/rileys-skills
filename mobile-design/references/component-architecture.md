# Component Architecture

Use this reference when keeping a multi-screen prototype coherent.

## The model

Apply this order:

1. Tokens
2. Primitives
3. Screens
4. Verify

## Tokens

Keep the global decisions in `styles.css`:

- colors
- fonts
- radius scale
- shadows
- spacing constants

If the accent or typography changes, prefer changing variables before changing component code.

## Primitives

Keep recurring UI in `primitives.jsx`:

- buttons
- chips
- cards
- icon wrappers
- avatar marks
- tab bar

If two screens render the same kind of object, make that object a primitive instead of restyling it twice.

## Screens

Keep composition in `screens.jsx`.

- screens should arrange primitives
- screens should not invent new token values casually
- screens can own one-off layout, copy, and flow logic

## Verify

After each meaningful pass, verify:

- top safe area clearance
- bottom CTA and tab bar clearance
- long title wrapping
- vertical spacing rhythm
- active and selected states

If you need automated checks or screenshots, pair this skill with `$playwright`.
