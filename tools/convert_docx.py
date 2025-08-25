#!/usr/bin/env python3
"""
Convert .docx files in the repository into code or Markdown, based on filename.

- *.py.docx -> *.py
- *.js.docx -> *.js
- other *.docx -> docs/<name>.md

Best-effort conversion using python-docx. Manual review is recommended.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable

try:
    from docx import Document  # type: ignore
except Exception as e:  # pragma: no cover
    sys.stderr.write(
        "python-docx is required. Install with: pip install -r requirements-dev.txt\n"
    )
    raise

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def iter_docx_files(paths: Iterable[Path]) -> Iterable[Path]:
    for p in paths:
        if p.is_dir():
            yield from iter_docx_files(p.iterdir())
        elif p.suffix.lower() == ".docx":
            yield p


def guess_output_path(src: Path) -> Path:
    name = src.name
    if name.endswith(".py.docx"):
        return src.with_suffix("")  # remove .docx -> *.py
    if name.endswith(".js.docx"):
        return src.with_suffix("")  # remove .docx -> *.js
    # general document -> docs/<base>.md
    base = name[:-5]  # strip .docx
    return DOCS / f"{base}.md"


def docx_to_markdown_text(doc: Document) -> str:
    # Very simple conversion: paragraphs and code-like runs
    lines: list[str] = []
    code_fence_open = False

    def open_code():
        nonlocal code_fence_open
        if not code_fence_open:
            lines.append("```")
            code_fence_open = True

    def close_code():
        nonlocal code_fence_open
        if code_fence_open:
            lines.append("```")
            code_fence_open = False

    for para in doc.paragraphs:
        style = (para.style.name or "").lower()
        text = para.text or ""
        if not text.strip():
            close_code()
            lines.append("")
            continue
        if any(k in style for k in ("code", "monospace", "pre")):
            open_code()
            lines.append(text)
        else:
            close_code()
            lines.append(text)
    close_code()
    return "\n".join(lines).strip() + "\n"


def convert_one(src: Path) -> Path:
    out = guess_output_path(src)
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = Document(str(src))
    text = docx_to_markdown_text(doc)

    # If target is .py/.js, try to strip markdown fences if present
    if out.suffix in {".py", ".js"}:
        # Extract fenced code blocks if any, otherwise dump raw text
        code_blocks = re.findall(r"```[a-zA-Z0-9_-]*\n(.*?)\n```", text, flags=re.S)
        content = "\n\n".join(cb.strip("\n") for cb in code_blocks) if code_blocks else text
        out.write_text(content, encoding="utf-8")
    else:
        out.write_text(text, encoding="utf-8")

    return out


def main() -> int:
    sources = list(iter_docx_files([ROOT]))
    if not sources:
        print("No .docx files found.")
        return 0
    print(f"Found {len(sources)} .docx file(s). Converting...")
    for src in sources:
        try:
            out = convert_one(src)
            print(f"[OK] {src} -> {out}")
        except Exception as e:  # pragma: no cover
            print(f"[FAIL] {src}: {e}")
    print("Done. Review outputs before committing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())