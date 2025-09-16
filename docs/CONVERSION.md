# Converting .docx files to code/docs

Some files in this repository were originally saved as Microsoft Word documents. This guide helps convert them into proper source files or Markdown while keeping the originals intact.

## Strategy

- Files ending with `.py.docx` become `.py` source files.
- Files ending with `.js.docx` become `.js` source files.
- Other `.docx` become Markdown (`docs/<name>.md`).

The converter uses `python-docx` to extract text. Please manually review the outputs.

## Usage

1. Create and activate a virtual environment (optional):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dev requirement:
   ```bash
   pip install -r requirements-dev.txt
   ```
3. Run the converter from the repo root:
   ```bash
   python tools/convert_docx.py
   ```

Outputs are written next to the source (for code) or into `docs/` (for general documents).

> Tip: Commit the generated files in a separate PR after you review them. Keep the original `.docx` files until you're confident the conversion is correct.
