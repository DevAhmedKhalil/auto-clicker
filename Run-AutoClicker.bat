@echo off
setlocal
cd /d "%~dp0"

rem 1) Prefer the standalone build (no Python needed)
if exist "%~dp0dist\AutoClicker.exe" (
    start "" "%~dp0dist\AutoClicker.exe"
    exit /b 0
)

rem 2) Fallback to the project venv
if exist "%~dp0venv\Scripts\pythonw.exe" (
    start "" "%~dp0venv\Scripts\pythonw.exe" "%~dp0auto_clicker_gui.py"
    exit /b 0
)

rem 3) Fallback to system Python
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0auto_clicker_gui.py"
    exit /b 0
)

where python >nul 2>nul
if %errorlevel%==0 (
    start "" python "%~dp0auto_clicker_gui.py"
    exit /b 0
)

echo [ERROR] Could not launch Auto Clicker.
echo - dist\AutoClicker.exe not found
echo - venv\Scripts\pythonw.exe not found
echo - no system Python found
echo.
echo To fix, either rebuild with:  python -m PyInstaller --noconfirm --clean AutoClicker.spec
echo Or install deps with:  pip install pyautogui pytz
pause
exit /b 1
