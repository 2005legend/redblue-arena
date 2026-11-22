import json
from pathlib import Path

from arena.config import load_config
from arena.events import EventLog
from arena.orchestrator import run_match
from arena.sandbox import ALLOWED_PORTS
from tests.fakes import FakeLLM, tc
from tests.test_blue import FIX, SEARCH, block

ROOT = Path(__file__).resolve().parent.parent
CFG = load_config(str(ROOT / "arena.yaml"))


def test_event_log_numbers_and_persists(tmp_path):
    log = EventLog(tmp_path / "e.jsonl")
    log.emit({"type": "a"}); log.emit({"type": "b"})
    rows = [json.loads(l) for l in (tmp_path / "e.jsonl").read_text().splitlines()]
    assert [r["seq"] for r in rows] == [0, 1] and all("ts" in r for r in rows)
    assert [e["type"] for e in log.events] == ["a", "b"]


def test_run_match_with_fakes(tmp_path):
    red = FakeLLM([
        tc("send_http_request", {"method": "POST", "path": "/api/login",
                                 "json": {"username": "alice", "password": "alice123"}}),
        tc("send_http_request", {"method": "GET", "path": "/api/invoices/3",
                                 "headers": {"Authorization": "Bearer tok-1"}}),
    ])
    blue = FakeLLM([{"content": block(SEARCH, FIX), "tool_calls": []}])
    log = EventLog(tmp_path / "events.jsonl")
    summary = run_match(CFG, red, blue, log, rounds=3, work_root=tmp_path / "work",
                        out_dir=tmp_path / "out", base_port=9900)
    types = [e["type"] for e in log.events]
    assert summary.closed == 1 and summary.total == 1 and summary.red == 1 and summary.blue == 1
    assert types.index("breach") < types.index("patched") < types.index("match_end")
    assert summary.final_port != summary.first_port
    assert (tmp_path / "out" / "hardened.patch").read_text().strip() != ""
    assert not ALLOWED_PORTS
