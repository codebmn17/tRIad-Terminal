from __future__ import annotations


def safe_md(text: str) -> str:
    """Very light sanitation for terminal rendering."""
    return text.replace("\r", "").strip()
