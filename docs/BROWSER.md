# Triad Browser: env/CLI usage

This project includes a helper CLI to open URLs, preferring Brave when available.

## Installation
- To install Brave, see docs/BRAVE.md or run `./scripts/install-brave.sh`.

## Environment variable
- TRIAD_BROWSER controls selection:
  - `auto` (default): attempt Brave if available; otherwise system default.
  - `brave`: force Brave (falls back to system if Brave is missing).
  - `system`: always use the system default browser.

```bash
# examples
export TRIAD_BROWSER=brave
export TRIAD_BROWSER=system
```

## CLI
Use the top-level script to open URLs and optionally request incognito/new window.

```bash
python triad_browser.py https://example.com
python triad_browser.py https://example.com --incognito
python triad_browser.py https://example.com --new-window
```

- When `TRIAD_BROWSER=auto`, the CLI will try Brave if flags are provided; otherwise it falls back to the default helper.
- When `TRIAD_BROWSER=brave`, the CLI invokes Brave directly.
- When `TRIAD_BROWSER=system`, it calls the OS default browser.