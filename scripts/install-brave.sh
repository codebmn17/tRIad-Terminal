#!/usr/bin/env bash
set -euo pipefail

OS_NAME="$(uname -s || echo unknown)"

if command -v brave-browser >/dev/null 2>&1 || \
   command -v brave >/dev/null 2>&1; then
  echo "[+] Brave already installed."
  exit 0
fi

case "$OS_NAME" in
  Darwin)
    if command -v brew >/dev/null 2>&1; then
      echo "[+] Installing Brave via Homebrew..."
      brew install --cask brave-browser
    else
      echo "[-] Homebrew not found. Install from https://brew.sh and re-run."
      exit 1
    fi
    ;;
  Linux)
    if command -v apt-get >/dev/null 2>&1; then
      echo "[+] Installing Brave on Debian/Ubuntu..."
      sudo apt-get update
      sudo apt-get install -y curl
      curl -fsS https://dl.brave.com/install.sh | sh
    elif command -v dnf >/dev/null 2>&1; then
      echo "[+] Installing Brave on Fedora..."
      sudo dnf install dnf-plugins-core -y
      sudo dnf config-manager --add-repo https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo
      sudo rpm --import https://brave-browser-rpm-release.s3.brave.com/brave-core.pub
      sudo dnf install -y brave-browser
    else
      echo "[-] Unsupported Linux distribution. See https://brave.com/linux/#linux for instructions."
      exit 1
    fi
    ;;
  MINGW*|MSYS*|CYGWIN*)
    echo "[i] Windows detected. Attempting winget..."
    if command -v winget >/dev/null 2>&1; then
      winget install --id=Brave.Brave -e || true
    elif command -v choco >/dev/null 2>&1; then
      choco install -y brave || true
    else
      echo "[-] Neither winget nor choco found. Install one and re-run."
      exit 1
    fi
    ;;
  *)
    echo "[-] Unsupported OS: $OS_NAME"
    exit 1
    ;;

esac

echo "[+] Brave installation attempt complete."
