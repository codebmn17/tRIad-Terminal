# Image Creation Guide (Triad Terminal)

Purpose
- Ensure a consistent, badass visual language that fits dark terminals and optional headers without sacrificing legibility.

Palette
- Neon Green: #39FF14 (primary strokes, accents)
- Slate 300–600: #CBD5E1–#475569 (secondary strokes, text)
- Backgrounds: nearly black (#0A0A0B), with subtle gradients/topographic noise

Sizing & Grids
- Icons: 128×128 viewBox; 2–3 px stroke; round caps/joins; minimal fills.
- Header emblems: 32–48 px height SVG in header; maintain 16 px margins.
- Wallpaper: 1920×1080+ PNG; corners darkened; 5–10% vignette for text contrast.

Effects
- Prefer CSS drop-shadow for glow over baked raster glows when possible.
- If rasterizing, export @1x, @2x, @3x PNGs.

File naming
- icons: assets/icons/<agent>.svg
- wallpaper: assets/images/triad-terminal-bg.png
- emblem: assets/images/geo-triad-triangle.png

Accessibility
- Keep sufficient contrast; avoid pure white on black; use slate tints for text.

Review checklist
- Does the icon read at 24 px?
- Is stroke width consistent across the set?
- Are margins and alignment consistent?
