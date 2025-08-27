# Contributing

Thanks for your interest in improving Triad Terminal!

## Development Environment

```bash
./scripts/dev-setup.sh
pre-commit install
```

## Code Style
- Python formatting: Ruff (format) + Black compatibility
- Linting: Ruff
- Typing: gradual; mypy is warn-only for now

## Branch & Commit
- Branches: `feature/<short-topic>`, `fix/<short-topic>`
- Commits: Conventional Commits (optional but encouraged), e.g., `feat: add repo CI`

## Pull Requests
- Ensure `ruff check` and `black --check` pass
- Include a brief description and testing notes
- Avoid moving or renaming existing modules unless coordinated (may break imports)

## Tests
- Placeholder. Add `pytest` in a future PR.