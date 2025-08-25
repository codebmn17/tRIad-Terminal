#!/usr/bin/env python3
"""
Triad Browser CLI helper

Usage:
  python triad_browser.py https://example.com [--incognito] [--new-window]

Config (env):
  TRIAD_BROWSER=auto|brave|system (default: auto)
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import webbrowser
from argparse import ArgumentParser
from pathlib import Path

# Reuse the existing helper when in auto mode
try:
    from utils.browser import open_url as open_url_auto  # type: ignore
except Exception:  # utils may not exist yet
    def open_url_auto(url: str) -> None:
        webbrowser.open(url)


def find_brave() -> str | None:
    candidates = [
        "brave-browser",
        "brave",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        str(Path(os.getenv("ProgramFiles(x86)", r"C:\\Program Files (x86)")).joinpath(
            "BraveSoftware", "Brave-Browser", "Application", "brave.exe"
        )),
        str(Path(os.getenv("ProgramFiles", r"C:\\Program Files")).joinpath(
            "BraveSoftware", "Brave-Browser", "Application", "brave.exe"
        )),
    ]
    for c in candidates:
        exe = shutil.which(c)
        if exe:
            return exe
        if os.path.isfile(c):
            return c
    return None


def open_with_brave(url: str, incognito: bool = False, new_window: bool = False) -> bool:
    brave = find_brave()
    if not brave:
        return False
    args = [brave]
    if incognito:
        args.append("--incognito")
    if new_window:
        args.append("--new-window")
    args.append(url)
    try:
        subprocess.Popen(args)
        return True
    except Exception:
        return False


def main(argv: list[str]) -> int:
    p = ArgumentParser(description="Triad Browser helper (Brave preferred)")
    p.add_argument("url", help="URL to open")
    p.add_argument("--incognito", action="store_true", help="Open in incognito/private mode")
    p.add_argument("--new-window", action="store_true", help="Open in a new window")
    args = p.parse_args(argv)

    mode = os.getenv("TRIAD_BROWSER", "auto").strip().lower()

    if mode not in {"auto", "brave", "system"}:
        mode = "auto"

    if mode == "brave":
        if open_with_brave(args.url, args.incognito, args.new_window):
            return 0
        # fallback to system if brave forced but missing
        webbrowser.open(args.url)
        return 0

    if mode == "system":
        webbrowser.open(args.url)
        return 0

    # auto: try brave with flags if provided, else use helper
    if args.incognito or args.new_window:
        if open_with_brave(args.url, args.incognito, args.new_window):
            return 0
    # fall back to helper auto mode
    open_url_auto(args.url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))