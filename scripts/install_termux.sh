#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

pkg update -y
pkg install -y python git clang make pkg-config openssl libffi

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-termux.txt

echo "OK: requirements installed for Termux (Android)."
