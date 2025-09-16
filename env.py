#!/usr/bin/env python3
"""Devcontainer writer utility for Triad Terminal."""

from __future__ import annotations

import json
from pathlib import Path

DEVCONTAINER = {
    "name": "Python Development",
    "image": "python:3.10",
    "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
    ],
    "settings": {"python.linting.enabled": True},
}


def write_devcontainer(target: str | Path = ".devcontainer/devcontainer.json") -> Path:
    """Create .devcontainer/devcontainer.json with standard settings."""
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(DEVCONTAINER, f, indent=2)
    return path


if __name__ == "__main__":
    out = write_devcontainer()
    print(f"Wrote {out}")
