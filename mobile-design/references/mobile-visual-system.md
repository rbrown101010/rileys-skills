# Mobile Visual System

Use this reference when tuning the feel of a mobile concept, especially from a blank slate.

## Core rules

1. Design inside a real device canvas. Default to `402x874` internal dimensions and scale the whole device to fit the browser window.
2. Respect safe areas. Keep headers clear of the top chrome and leave enough room for the home indicator at the bottom.
3. Keep touch targets at `44px` minimum. Primary buttons should usually land in the `52px` to `56px` range.
4. Use a restrained type scale:
   - Display: `30px` to `38px`
   - Section title: `16px` to `17px`
   - Body: `14px` to `15px`
   - Metadata: `11px` to `13px`
5. Use an `8px` spacing rhythm. Common gaps: `8`, `10`, `12`, `14`, `16`, `20`.
6. Build hierarchy with contrast first. Keep the text tiers stable and avoid inventing new grays per screen.
7. Use one accent color sparingly. Save it for CTA, selection, active navigation, and high-signal highlights.
8. Prefer simple, geometric avatar or brand marks over fussy illustration.
9. Keep motion subtle. `150ms` to `200ms` is enough for tap feedback and screen polish.
10. Decide the system once and apply it everywhere. Drift usually comes from inconsistency, not from any single wrong value.

## Defaults in the starter

- Background: near-black with warm text
- Accent: warm amber
- UI font: `Inter Tight`
- Display font: `Instrument Serif`
- Mono: `IBM Plex Mono`

These are starting points, not hard requirements. Change the variables in `styles.css` first, then let components inherit.
