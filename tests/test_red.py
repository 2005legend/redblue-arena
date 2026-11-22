from pathlib import Path

from arena.config import load_config
from arena.red import run_red
from arena.sandbox import PortAllocator, TargetProcess
from tests.fakes import FakeLLM, tc

ROOT = Path(__file__).resolve().parent.parent
CFG = load_config(str(ROOT / "arena.yaml"))
USERS = CFG.users


def target(tmp_path, port):
    t = TargetProcess(CFG.app_dir, CFG.seed_db, port, tmp_path)
    t.prepare(); t.start()
    return t


def test_red_records_breach(tmp_path):
    t = target(tmp_path, PortAllocator(9600).next())
    events = []
    try:
        llm = FakeLLM([
            tc("send_http_request", {"method": "POST", "path": "/api/login",
                                     "json": {"username": "alice", "password": "alice123"}}),
            tc("send_http_request", {"method": "GET", "path": "/api/invoices/3",
                                     "headers": {"Authorization": "Bearer tok-1"}}),
        ])
        exploits = run_red(llm, t.url, {"paths": {}}, USERS, events.append, max_steps=10)
    finally:
        t.stop()
    assert [e.flag for e in exploits] == ["FLAG{idor_invoice_leak}"]
    assert exploits[0].vuln_class == "idor"
    breach = [e for e in events if e["type"] == "breach"]
    assert breach and breach[0]["route"] == "/api/invoices/{id}"


def test_red_survives_bad_tool_args(tmp_path):
    t = target(tmp_path, PortAllocator(9610).next())
    events = []
    try:
        llm = FakeLLM([
            tc("send_http_request", None, raw="{not json"),
            tc("send_http_request", {"method": "GET", "path": "/api/search",
                                     "params": {"q": "' OR 1=1--"}}),
        ])
        exploits = run_red(llm, t.url, {"paths": {}}, USERS, events.append, max_steps=10)
    finally:
        t.stop()
    assert any(e["type"] == "red_error" for e in events)
    assert exploits and exploits[0].vuln_class == "sqli"


def test_red_stops_at_max_steps(tmp_path):
    llm = FakeLLM([tc("discover_routes", {}) for _ in range(20)])
    run_red(llm, "http://127.0.0.1:1", {"paths": {}}, USERS, lambda e: None, max_steps=3)
    assert llm.calls == 3
