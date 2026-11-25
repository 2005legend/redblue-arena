@echo off
REM ============================================================
REM  Cold-cache LIVE LLM match on the demo site (Lumen Goods).
REM  Blue's model writes fresh patches from scratch - costs tokens.
REM
REM  Requires an API key: open .env and set ARENA_API_KEY
REM  (and ARENA_BASE_URL if not OpenAI-compatible).
REM ============================================================
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo No venv - run run_arena.bat first.
    pause
    exit /b 1
)

if not exist .env (
    echo No .env found - creating from template:
    copy .env.example .env >nul
)
findstr /R /C:"^ARENA_API_KEY=[^ ].*" .env >nul
if errorlevel 1 (
    echo.
    echo  No API key yet. Open .env in this folder and set:
    echo     ARENA_API_KEY=sk-...
    echo     ARENA_BASE_URL=https://api.openai.com/v1   (optional non-OpenAI)
    echo  Then run this script again.
    notepad .env
    pause
    exit /b 1
)

set ARENA_CONFIG=arena.demo.yaml
set ARENA_KEEP_TARGET=1
echo.
echo Cold-cache demo match on fixtures\demo_shop ...
echo (deletes patches\cache.demo.json so Blue must write fresh patches)
copy /y patches\cache.demo.json patches\cache.demo.json.judges.bak >nul 2>&1
del patches\cache.demo.json 2>nul
.venv\Scripts\python.exe -m arena.cli run --config arena.demo.yaml --yes
if exist matches\report.md echo.
echo Finished - outputs are in matches\<run-id>\  (hardened.patch, report.md, tests\security\)
echo Warm cache restored? Run: copy /y patches\cache.demo.json.judges.bak patches\cache.demo.json
pause
