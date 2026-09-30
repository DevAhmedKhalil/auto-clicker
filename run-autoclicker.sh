#!/usr/bin/env bash
# Launcher for macOS / Linux (equivalent of Run-AutoClicker.bat on Windows).
set -euo pipefail
cd "$(dirname "$0")"

# 1) Standalone PyInstaller build (no Python needed).
#     NOTE: PyInstaller binaries are OS-specific — build on each OS with:
#       python3 -m pip install pyinstaller
#       python3 -m PyInstaller --noconfirm --clean AutoClicker.spec
if [ "$(uname)" = "Darwin" ] && [ -d "dist/AutoClicker.app" ]; then
    open "dist/AutoClicker.app"
    exit 0
fi
if [ -x "dist/AutoClicker" ]; then
    exec "dist/AutoClicker"
fi

# 2) Project virtualenv.
if [ -x "venv/bin/python" ]; then
    exec "venv/bin/python" "auto_clicker_gui.py"
fi

# 3) System Python.
if command -v python3 >/dev/null 2>&1; then
    exec python3 "auto_clicker_gui.py"
fi

echo "[ERROR] python3 not found." >&2
echo "Install Python 3, then:  pip install -r requirements.txt" >&2
exit 1
