# Architecture Overview

Triad Terminal brings together several domains:

- Shell Interface: interactive shell, environment management, aliases, history
- Repository Manager: local Git operations and optional GitHub API integration
- Security System: user/session management, password policy, 2FA hooks
- Voice & AI: text-to-speech engines, recognition stubs, AI helpers
- UI/Theme: terminal UI, themes, and visual helpers

## Current State

- Multiple modules exist with Version1/Version2 suffixes. They coexist for backward compatibility and experimentation.
- Entry points include scripts like `triad-terminal.py` and `optimized_terminal.py`.

## Suggested Future Layout (not implemented in this PR)

```
src/triad_terminal/
  __init__.py
  app.py              # main app orchestration
  shell/
  repo/
  security/
  voice/
  ai/
  ui/
```

## Data & Secrets

- Avoid committing secrets. Use environment variables or local `.env` files (ignored).

## Logging

- Python logging is configured in the main entrypoints; CI does not ship logs.