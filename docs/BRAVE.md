# Brave Browser Integration

Triad Terminal can optionally prefer Brave Browser for opening web links while falling back to the system default browser if Brave is not available.

## Install Brave

- macOS (Homebrew):
  ```bash
  brew install --cask brave-browser
  ```
- Windows (winget):
  ```powershell
  winget install --id=Brave.Brave -e
  ```
  or Chocolatey:
  ```powershell
  choco install brave
  ```
- Debian/Ubuntu:
  ```bash
  sudo apt update
  sudo apt install -y curl
  curl -fsS https://dl.brave.com/install.sh | sh
  ```
- Fedora (dnf):
  ```bash
  sudo dnf install dnf-plugins-core -y
  sudo dnf config-manager --add-repo https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo
  sudo rpm --import https://brave-browser-rpm-release.s3.brave.com/brave-core.pub
  sudo dnf install -y brave-browser
  ```

Alternatively, run the helper script:

```bash
./scripts/install-brave.sh
```

## Using Brave programmatically

Use the browser helper to open URLs. It will prefer Brave if available, otherwise it uses the system default.

```python
from utils.browser import open_url

open_url("https://example.com")
```