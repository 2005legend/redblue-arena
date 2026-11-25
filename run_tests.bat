@echo off
REM Run the full pytest suite (99 tests, ~6 min).
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo No venv - run run_arena.bat first (it creates one).
    pause
    exit /b 1
)
.venv\Scripts\python.exe -m pytest tests -q
echo.
echo Note: tests\test_capture.py can flake with WinError 145 inside a full
echo one-process Windows run - it passes alone (pytest tests\test_capture.py -q).
pause
