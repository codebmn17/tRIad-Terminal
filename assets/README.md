# Triad Terminal Assets

This directory contains image assets for the Triad Terminal UI theming system.

## Required Images

To enable the full Triad Terminal theme, place the following images in this directory:

### Background Wallpaper
- **Filename:** `triad-terminal-bg.png`
- **Description:** The dark cyberpunk wallpaper shown in the terminal background
- **Recommended resolution:** 1920x1080 or higher
- **Format:** PNG (supports transparency)
- **Notes:** This image will be used as the body background with a gradient overlay

### Triangle Emblem
- **Filename:** `triad-triangle.svg` (preferred) or `triad-triangle.png`
- **Description:** The neon green triangle emblem shown on the right side of the header
- **Recommended size:** 32x32 to 64x64 pixels
- **Format:** SVG (vector, preferred) or PNG (raster)
- **Style:** Neon green wireframe triangle with glow effect
- **Notes:** Should match the cyberpunk aesthetic with bright green (#00ff9f) colors

### Mask Icon (Optional)
- **Filename:** `anon-mask.svg`
- **Description:** Anonymous mask icon for the left side of the header
- **Notes:** If not provided, this icon will be omitted from the header

## How to Enable the Theme

1. Drop the required image files into this `/assets/images/` directory
2. Include the CSS file in your HTML: `<link rel="stylesheet" href="/web/ui/theme/theme-triad.css">`
3. Include the JS file in your HTML: `<script src="/web/ui/theme/init-triad-theme.js"></script>`
4. Optionally use the header component: see `/web/ui/components/header.html`

## Fallback Behavior

- If `triad-terminal-bg.png` is missing: Falls back to a dark gradient background
- If `triad-triangle.svg` is missing: Uses the provided placeholder triangle
- If `anon-mask.svg` is missing: Left side of header shows only title

## Theme Integration

The theme is designed to work with:
- **Web applications** (HTML/CSS/JS)
- **Electron apps** (desktop applications)
- **PyWebView** (Python web view applications)
- Any web-based terminal or dashboard interface

For detailed integration instructions, see `/docs/THEME.md`.