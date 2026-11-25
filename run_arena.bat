@echo off
REM ============================================================
REM  Vibe Arena - one-click setup + launch (Windows)
REM  Default target: fixtures/demo_shop (Lumen Goods, FastAPI+SQLite)
REM
REM  NO API KEY NEEDED for the replay demo - judges can run everything.
REM  For a LIVE LLM match: put your key in .env as ARENA_API_KEY
REM  (and optionally ARENA_BASE_URL if not OpenAI), then use
REM  run_cold_llm.bat
REM ============================================================
setlocal
cd /d "%~dp0"
set PYTHON=.venv\Scripts\python.exe

echo ============================================
echo  [1/4] Python venv + dependencies
echo ============================================
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv || goto :pyerr
)
if not exist %PYTHON% (
    echo venv exists but python missing - recreating...
    rmdir /s /q .venv
    python -m venv .venv || goto :pyerr
)
%PYTHON% -m pip install --quiet -r requirements.txt || goto :pyerr
echo OK - dependencies installed

echo ============================================
echo  [2/4] Config
echo ============================================
REM Default demo target (Lumen Goods). Change arena.demo.yaml to retarget.
set ARENA_CONFIG=arena.demo.yaml
REM Leave the patched site browsable after the match ends.
set ARENA_KEEP_TARGET=1
REM Seed match data (idempotent).
%PYTHON% fixtures\demo_shop\seed.py
if not exist .env (
    copy .env.example .env >nul
    echo.
    echo   Created .env  ->  for a LIVE LLM match, paste your key there:
    echo     ARENA_API_KEY=sk-...
    echo     ARENA_BASE_URL=https://api.openai.com/v1     (optional)
    echo   Without a key everything still runs in replay mode - no problem.
)
echo OK - config ready (%ARENA_CONFIG%)

echo ============================================
echo  [3/4] Health: run the test suite? (recommended first time)
echo ============================================
choice /C YN /M "Run the 99-test pytest suite now (about 6 min)"
if errorlevel 2 goto :skip_tests
%PYTHON% -m pytest tests -q || goto :pyerr
echo OK - all tests pass
:skip_tests

echo ============================================
echo  [4/4] Launch: server (8765) + UI (5173) + browser
echo ============================================
start "Vibe Arena server (8765)" cmd /k "%PYTHON% -m arena.cli serve"
pushd ui
if not exist node_modules (
    echo Installing UI dependencies (first run only)...
    call npm install
)
start "Vibe Arena UI (5173)" cmd /k "npm run dev"
popd
timeout /t 4 /nobreak >nul
start "" http://localhost:5173
echo.
echo   UP AND RUNNING
echo     Arena UI:        http://localhost:5173   <-- click Start here
echo     Full victim site: http://127.0.0.1:8765/target
echo     Recorded match (no key): http://127.0.0.1:8765 replay mode in the UI
echo.
echo   Next: in the Arena UI press Start - sweep finds the bugs,
echo   Blue patches, the live victim site flips leak - BLOCKED.
echo.
pause
exit /b 0

:pyerr
echo.
echo  ERROR: setup failed. Is Python 3.11+ on PATH? Try: python --version
pause
exit /b 1
