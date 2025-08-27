"""
Utilities to launch URLs, preferring Brave Browser if available.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Optional


def _find_brave_executable() -> Optional[str]:
    candidates = [
        "brave-browser",  # common on Linux
        "brave",          # alternative on Linux/macOS
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",  # macOS
        str(Path(os.getenv("ProgramFiles(x86)", r"C:\\Program Files (x86)")).joinpath(
            "BraveSoftware", "Brave-Browser", "Application", "brave.exe"
        )),
        str(Path(os.getenv("ProgramFiles", r"C:\\Program Files")).joinpath(
            "BraveSoftware", "Brave-Browser", "Application", "brave.exe"
        )),
    ]

    for c in candidates:
        if shutil.which(c):
            return shutil.which(c)
        if os.path.isfile(c):
            return c
    return None


def open_url(url: str) -> None:
    """Open a URL in Brave if available, otherwise default system browser.

    Parameters
    ----------
    url: str
        The URL to open.
    """
    brave = _find_brave_executable()
    if brave:
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen([brave, url], shell=False)
            else:
                subprocess.Popen([brave, url])
            return
        except Exception:
            pass
    # Fallback
    webbrowser.open(url)