#!/usr/bin/env python3
"""
Export SVG icons in assets/icons/ to PNGs at common sizes.
Optional dependency: cairosvg
Usage:
  python assets/tools/export_icons.py --sizes 24 32 48 64 96 128
"""
from __future__ import annotations

import argparse
import glob
import os

try:
    import cairosvg  # type: ignore
except Exception:  # pragma: no cover
    cairosvg = None


def export(svg_path: str, sizes: list[int]) -> None:
    base, _ = os.path.splitext(svg_path)
    for sz in sizes:
        out = f"{base}-{sz}.png"
        if cairosvg is None:
            print(f"[skip] cairosvg not installed; would export {svg_path} -> {out}")
            continue
        with open(svg_path, "rb") as f:
            data = f.read()
        cairosvg.svg2png(bytestring=data, write_to=out, output_width=sz, output_height=sz)
        print(f"[ok] {out}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", nargs="*", type=int, default=[24, 32, 48, 64, 96, 128])
    args = p.parse_args()

    svgs = sorted(glob.glob(os.path.join("assets", "icons", "*.svg")))
    if not svgs:
        print("No SVG icons found in assets/icons/")
        return 1
    for svg in svgs:
        export(svg, args.sizes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
