# Triad Terminal

A Python-first, extensible terminal environment that integrates:
- Enhanced shell and environment helpers
- Git repository management with optional GitHub integration
- Security/auth (session, password, optional biometrics groundwork)
- Voice assistant (TTS/ASR stubs and engines) and AI integration
- Theming/UI utilities and installers

> Note: The repository currently contains multiple Version1/Version2 modules. Consolidation into a single package is planned but not part of this PR to avoid breaking changes.

## Quick start

Prerequisites: Python 3.11+ recommended (3.12 supported).

```bash
# Clone (private repo)
git clone git@github.com:codebmn17/tRIad-Terminal.git
cd tRIad-Terminal

# Optional: set up a venv and dev tools
./scripts/dev-setup.sh

# Run the main entry (one of the current entry scripts)
python triad-terminal.py
# or
python optimized_terminal.py
```

## Web browsing (Brave preferred)

We ship a small helper that prefers Brave Browser if installed and falls back to the system default. See docs/BRAVE.md for installation instructions.

```python
from utils.browser import open_url
open_url("https://example.com")
```

## Converting .docx artifacts

If you see files like `main.py.docx` or `devenv.js.docx`, use the converter to generate proper source files while keeping the originals:

```bash
pip install -r requirements-dev.txt
python tools/convert_docx.py
```

See docs/CONVERSION.md for details.

## Development

- Formatting and linting: Ruff + Black (configured via pyproject.toml)
- Pre-commit hooks: see .pre-commit-config.yaml
- CI: GitHub Actions runs lint checks on push/PR