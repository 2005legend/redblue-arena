@echo off
cd /d "C:\Users\USER\sidaarth\compute50 hackathon\vibe-arena\fixtures\dev_target"
set ARENA_DB=seed.db
python -m uvicorn app.main:app --port 8090 --log-level warning
