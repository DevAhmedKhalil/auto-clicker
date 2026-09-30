# Auto-Clicker

Cross-platform (Windows / macOS / Linux) auto-clicker with a Tkinter GUI.

Main app: `auto_clicker_gui.py` — 4 modes:

- **Mode 1** — every-minute click + fill click, 5-minute marks use a special click
- **Mode 2** — click every 5 min + one extra click 2.5 min later
- **Mode 3** — alternate between two recorded screen positions (odd/even minute)
- **Mode 4** — click at specific seconds of every minute (e.g. `0,30`)

Each click type has its own beep sound (Windows), terminal bell elsewhere.
Sounds can be toggled with the 🔔 Sound checkbox.

Legacy console scripts (`autoClicker.py`, `clickerAtDivBy5.py`,
`twoScreensAutoClicker.py`) also work on all three OSes.

## Requirements

- Python 3.10+
- Dependencies in `requirements.txt` (`pyautogui`, `pytz`)

```sh
pip install -r requirements.txt
```

OS extras:

- **Windows** — nothing extra. Double-click `Run-AutoClicker.bat`
  (uses `dist\AutoClicker.exe` if present, else the venv, else system Python).
- **macOS** — grant permission once for the terminal/app that runs it:
  *System Settings → Privacy & Security → Accessibility* (mouse control)
  and *Screen Recording* (some `pyautogui` features). Then:
  ```sh
  chmod +x run-autoclicker.sh
  ./run-autoclicker.sh
  ```
- **Linux (Debian/Ubuntu)** — Tkinter + screenshot backend first:
  ```sh
  sudo apt install python3-tk python3-dev scrot
  pip install -r requirements.txt
  chmod +x run-autoclicker.sh
  ./run-autoclicker.sh
  ```
  On Wayland, `pyautogui` mouse control may need an X11 session.

## Run from source (any OS)

```sh
python auto_clicker_gui.py
```

## Standalone build (optional)

PyInstaller binaries are **OS-specific**: a Windows `.exe` will NOT run on
macOS/Linux. Build on each machine separately:

```sh
pip install pyinstaller
python -m PyInstaller --noconfirm --clean AutoClicker.spec
```

Output lands in `dist/` (`AutoClicker.exe` on Windows,
`AutoClicker` / `AutoClicker.app` on macOS/Linux).

## Moving to another machine (Mac / Linux)

Copy only the source — skip the heavy/OS-specific stuff:

- ✅ copy: `*.py`, `*.spec`, `*.sh`, `*.bat`, `requirements.txt`,
  `.gitattributes`, `README.md`
- ❌ skip: `venv/`, `dist/`, `build/`, `__pycache__/`

Then on the new machine: install Python 3, `pip install -r requirements.txt`,
and run (`./run-autoclicker.sh` or `python3 auto_clicker_gui.py`).
