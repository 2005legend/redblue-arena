"""WebSocket + HTTP server for the arena UI: live matches, replays, and downloads."""
import asyncio
import io
import json
import re
import threading
import time
import zipfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

MATCHES = Path("matches")
STATE: dict = {"log": None, "match_id": None, "thread": None}

app = FastAPI(title="Vibe Arena server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/match/current")
def current():
    running = bool(STATE["thread"] and STATE["thread"].is_alive())
    return {"match_id": STATE["match_id"], "running": running}


@app.post("/api/match/start")
def start_match(config: str = "arena.yaml"):
    if STATE["thread"] and STATE["thread"].is_alive():
        raise HTTPException(409, "a match is already running")
    from arena.config import load_config
    from arena.events import EventLog
    from arena.llm import LLM
    from arena.orchestrator import run_match

    match_id = "live-" + time.strftime("%Y%m%d-%H%M%S")
    log = EventLog(MATCHES / match_id / "events.jsonl")
    cfg = load_config(config)
    STATE.update(log=log, match_id=match_id)
    t = threading.Thread(target=run_match, daemon=True, kwargs=dict(
        cfg=cfg, llm_red=LLM("red"), llm_blue=LLM("blue"), log=log,
        out_dir=MATCHES / match_id, work_root=Path("work") / match_id))
    STATE["thread"] = t
    t.start()
    return {"match_id": match_id}


@app.websocket("/ws")
async def ws(socket: WebSocket, replay: str | None = None, speed: float = 1.0):
    await socket.accept()
    try:
        if replay:
            path = (MATCHES / replay).resolve()
            if not str(path).startswith(str(MATCHES.resolve())) or not path.is_file():
                await socket.send_json({"type": "error", "text": "replay not found"})
                return
            prev = 0.0
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                e = json.loads(line)
                await asyncio.sleep(min(max((e.get("ts", prev) - prev) / max(speed, 0.1), 0), 2.0))
                prev = e.get("ts", prev)
                await socket.send_json(e)
            return
        log = STATE["log"]
        if log is None:
            await socket.send_json({"type": "idle"})
            return
        q = log.subscribe(asyncio.get_running_loop())
        backlog = list(log.events)
        for e in backlog:
            await socket.send_json(e)
        while True:
            e = await q.get()
            if e["seq"] < len(backlog):
                continue
            await socket.send_json(e)
            if e["type"] == "match_end":
                return
    except WebSocketDisconnect:
        pass


@app.get("/api/export/{match_id}/{name}")
def download(match_id: str, name: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", match_id):
        raise HTTPException(400, "bad match id")
    base = MATCHES / match_id
    if name == "security_tests.zip":
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for f in sorted((base / "tests" / "security").glob("*.py")):
                z.write(f, f.name)
        return Response(buf.getvalue(), media_type="application/zip")
    if name not in ("hardened.patch", "report.md") or not (base / name).is_file():
        raise HTTPException(404, "not found")
    return FileResponse(base / name, filename=name)
