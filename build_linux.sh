#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt

pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "i-told-u" \
  app.py

echo "Build ready: dist/i-told-u/i-told-u"
