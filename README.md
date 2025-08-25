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

## Development

- Formatting and linting: Ruff + Black (configured via pyproject.toml)
- Pre-commit hooks: see .pre-commit-config.yaml
- CI: GitHub Actions runs lint checks on push/PR

## Project layout (selected)

```
.
├── .github/workflows/         # CI workflows
├── docs/                      # Architecture and contribution docs
├── scripts/                   # Dev helper scripts
├── *.py                       # Existing Python modules (Version1/Version2 coexist)
├── *.js, *.sh                 # Installer/runner helpers
└── README.md
```

## Roadmap (proposed)
- Package under src/triad_terminal/ with typed modules
- Single, canonical implementations (remove Version* duplicates)
- Add tests and coverage gates in CI
- Optional releases and packaging if distribution is desired