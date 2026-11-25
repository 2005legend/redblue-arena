"""WebSocket + HTTP server for the arena UI: live matches, replays, and downloads."""
import asyncio
import io
import json
import os
import re
import threading
import time
import zipfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from arena import site_api

MATCHES = Path("matches")
CONFIG = os.environ.get("ARENA_CONFIG", "arena.yaml")
STATIC = Path(__file__).with_name("static")
STATE: dict = {"log": None, "match_id": None, "thread": None}

app = FastAPI(title="Vibe Arena server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/match/current")
def current():
    running = bool(STATE["thread"] and STATE["thread"].is_alive())
    return {"match_id": STATE["match_id"], "running": running}


def _battle(match: dict) -> dict:
    data = site_api._public(match)
    try:
        data["replay"] = Path(match["_source"]).resolve().relative_to(
            MATCHES.resolve()).as_posix()
    except ValueError:
        data["replay"] = Path(match["_source"]).name
    return data


@app.get("/api/battles")
def battles():
    return [_battle(m) for m in site_api.list_matches(MATCHES)]


@app.get("/api/battles/{battle_id}")
def battle(battle_id: str):
    match = next((m for m in site_api.list_matches(MATCHES) if m["id"] == battle_id), None)
    if not match:
        raise HTTPException(404, "battle not found")
    return _battle(match)


@app.get("/api/battles/{battle_id}/report")
def battle_report(battle_id: str):
    rep = site_api.report(MATCHES, battle_id)
    if rep is None:
        raise HTTPException(404, "battle not found")
    return rep


@app.post("/api/battles/{battle_id}/{action}")
def battle_control(battle_id: str, action: str):
    raise HTTPException(409, "battles are recorded live runs; start one with POST /api/match/start")


@app.get("/api/dashboard/stats")
def dashboard_stats():
    return site_api.dashboard(MATCHES)


@app.get("/api/vulnerabilities")
def vulnerability_list():
    return site_api.vulnerabilities(MATCHES)


@app.get("/api/patches")
def patch_list():
    return site_api.patches(MATCHES)


@app.get("/api/target/config/status")
def target_config_status():
    from arena.config import load_config
    try:
        cfg = load_config(CONFIG)
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(503, f"arena config unavailable: {exc}")
    return site_api.target_status(cfg, MATCHES)


@app.post("/api/target/{rest:path}")
def target_control(rest: str):
    raise HTTPException(503, "the arena exposes read-only target status; the target app only runs "
                             "inside a match sandbox, so there is no exploit console or mode switch")


@app.get("/target")
def live_target_page():
    """Full-screen victim view: the real target site plus a live attack feed."""
    return FileResponse(STATIC / "target.html")


@app.get("/api/target/live")
def target_live():
    """Where the currently running (or kept-alive) target is listening, if anywhere.

    The match a `serve` process started is checked first; otherwise the newest recorded run is
    used, so a match started from the CLI is visible here too, and a target kept alive with
    ARENA_KEEP_TARGET=1 stays reachable after a server restart.
    """
    mid = STATE.get("match_id")
    base = {"url": None, "port": None, "alive": False, "match_id": mid,
            "running": bool(STATE["thread"] and STATE["thread"].is_alive())}
    found = site_api.live_target(MATCHES, mid) if mid else {"alive": False}
    if not found.get("alive"):
        found = site_api.live_target(MATCHES)
    if not found.get("alive") or not found.get("url"):
        return base
    return {**base, "url": found["url"], "port": found["port"], "alive": True,
            "match_id": found.get("match_id") or mid}


@app.post("/api/match/start")
def start_match(config: str | None = None):
    config = config or CONFIG
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
        out_dir=MATCHES / match_id, work_root=Path("work") / match_id,
        keep_target=os.environ.get("ARENA_KEEP_TARGET", "0") == "1"))
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
                if e.get("type") == "match_start":
                    e = {**e, "sample": True}  # a replay is never a live run; say so on screen
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
            # Marked so the victim page can tell history from a live attack: replaying a past
            # breach against today's target would show a state that never happened.
            await socket.send_json({**e, "backlog": True})
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
