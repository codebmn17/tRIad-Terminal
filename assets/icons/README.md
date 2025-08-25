# Triad Icons — Usage and Standards

- Format: SVG (preferred). PNGs can be exported for platforms that need raster.
- Size: Author at 128×128 viewBox; render crisply at 24–128 px.
- Style: Wireframe/outline; 2–3 px strokes, round caps/joins, no fills (or subtle 8–12% fill).
- Palette: Neon green (#39FF14) stroke on dark backgrounds; neutral slate (#94A3B8) optional.
- Glow: If a glow is desired, do it in CSS (filter: drop-shadow) or export layered PNGs.

Icons
- orchestrator.svg — triangle + resonance arcs
- planner.svg — gear + node lattice
- critic.svg — shield + exclamation
- executor.svg — forward chevron/bolt

Terminal mapping (fallbacks)
- ASCII: ^ for Orchestrator, * for Planner, ! for Critic, > for Executor
- Nerd Font examples: nf-md-triangle, nf-md-cog, nf-md-shield_alert, nf-md-flash

Export
- Optional tool: assets/tools/export_icons.py to render PNGs at 24/32/48/64/96/128 if cairosvg is installed.