import json
from pathlib import Path

from arena.config import load_config
from arena.events import EventLog
from arena.llm import BudgetExceeded
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
                        out_dir=tmp_path / "out", base_port=9900, strategy="llm",
                        cache_path=tmp_path / "cache.json")
    types = [e["type"] for e in log.events]
    assert summary.closed == 1 and summary.total == 1 and summary.red == 1 and summary.blue == 1
    assert types.index("breach") < types.index("patched") < types.index("match_end")
    assert summary.final_port != summary.first_port
    assert (tmp_path / "out" / "hardened.patch").read_text().strip() != ""
    assert not ALLOWED_PORTS


def test_budget_exhaustion_ends_the_match_with_exports(tmp_path):
    red = FakeLLM([
        tc("send_http_request", {"method": "POST", "path": "/api/login",
                                 "json": {"username": "alice", "password": "alice123"}}),
        tc("send_http_request", {"method": "GET", "path": "/api/invoices/3",
                                 "headers": {"Authorization": "Bearer tok-1"}}),
    ])
    blue = FakeLLM([BudgetExceeded("token budget 100 exhausted (120 tokens used)")])
    log = EventLog(tmp_path / "events.jsonl")
    summary = run_match(CFG, red, blue, log, rounds=3, work_root=tmp_path / "work",
                        out_dir=tmp_path / "out", base_port=9910, strategy="llm",
                        cache_path=tmp_path / "cache.json")
    types = [e["type"] for e in log.events]
    assert "breach" in types and "budget_exceeded" in types and types[-1] == "match_end"
    assert summary.red == 1 and summary.closed == 0
    assert (tmp_path / "out" / "hardened.patch").is_file()
    assert not ALLOWED_PORTS


def test_red_budget_exhaustion_ends_the_match_with_exports(tmp_path):
    red = FakeLLM([BudgetExceeded("token budget 100 exhausted (120 tokens used)")])
    blue = FakeLLM([])
    log = EventLog(tmp_path / "events.jsonl")
    summary = run_match(CFG, red, blue, log, rounds=2, work_root=tmp_path / "work",
                        out_dir=tmp_path / "out", base_port=9920, strategy="llm",
                        cache_path=tmp_path / "cache.json")
    types = [e["type"] for e in log.events]
    assert "budget_exceeded" in types and types.index("budget_exceeded") < types.index("match_end")
    assert summary.red == 0 and summary.total == 0
    assert (tmp_path / "out" / "hardened.patch").is_file()
    assert not ALLOWED_PORTS


SQL_OLD = '''    sql = f"SELECT id, name FROM products WHERE hidden = 0 AND name LIKE '%{q}%'"
    try:
        rows = conn.execute(sql).fetchall()'''
SQL_FIX = '''    sql = "SELECT id, name FROM products WHERE hidden = 0 AND name LIKE ?"
    try:
        rows = conn.execute(sql, (f"%{q}%",)).fetchall()'''
ADMIN_OLD = '''    current_user(authorization)
    conn = get_conn()'''
ADMIN_FIX = '''    user = current_user(authorization)
    assert user["role"] == "admin", "admin only"
    conn = get_conn()'''
TRAV_OLD = '''    path = Path("files") / name
    if not path.is_file():'''
TRAV_FIX = '''    base = Path("files").resolve()
    path = (base / name).resolve()
    if base not in path.parents or not path.is_file():'''


def test_sweep_match_closes_all_four_bugs_with_zero_red_tokens(tmp_path):
    red = FakeLLM([])
    blue = FakeLLM([
        {"content": block(SQL_OLD, SQL_FIX), "tool_calls": []},
        {"content": block(SEARCH, FIX), "tool_calls": []},
        {"content": block(ADMIN_OLD, ADMIN_FIX, "app/routes/admin.py"), "tool_calls": []},
        {"content": block(TRAV_OLD, TRAV_FIX, "app/routes/files.py"), "tool_calls": []},
    ])
    log = EventLog(tmp_path / "events.jsonl")
    summary = run_match(CFG, red, blue, log, rounds=3, work_root=tmp_path / "work",
                        out_dir=tmp_path / "out", base_port=9930, strategy="sweep",
                        cache_path=tmp_path / "cache.json")
    types = [e["type"] for e in log.events]
    assert summary.sweep_findings == 4 and summary.red == 4 and summary.closed == 4
    assert summary.tokens == 0 and red.calls == 0 and summary.llm_calls == blue.calls == 4
    assert types.index("sweep_start") < types.index("breach") < types.index("sweep_done")
    assert types.index("sweep_done") < types.index("patched")
    assert types.count("patched") == 4 and types[-1] == "match_end"
    assert {e["source"] for e in log.events if e["type"] == "breach"} == {"sweep"}
    assert log.events[0]["strategy"] == "sweep"
    assert not ALLOWED_PORTS


def test_blue_provider_outage_does_not_abort_the_match(tmp_path):
    red = FakeLLM([
        tc("send_http_request", {"method": "POST", "path": "/api/login",
                                 "json": {"username": "alice", "password": "alice123"}}),
        tc("send_http_request", {"method": "GET", "path": "/api/invoices/3",
                                 "headers": {"Authorization": "Bearer tok-1"}}),
    ])
    blue = FakeLLM([RuntimeError("all models failed: m: 429")])
    log = EventLog(tmp_path / "events.jsonl")
    summary = run_match(CFG, red, blue, log, rounds=1, work_root=tmp_path / "work",
                        out_dir=tmp_path / "out", base_port=9950, strategy="llm",
                        cache_path=tmp_path / "cache.json")
    types = [e["type"] for e in log.events]
    assert "breach" in types and "blue_error" in types and types[-1] == "match_end"
    assert summary.red == 1 and summary.closed == 0
    assert (tmp_path / "out" / "hardened.patch").is_file()
    assert not ALLOWED_PORTS


def test_hybrid_skips_the_red_llm_when_the_sweep_finds_bugs(tmp_path):
    red = FakeLLM([])
    blue = FakeLLM([
        {"content": block(SQL_OLD, SQL_FIX), "tool_calls": []},
        {"content": block(SEARCH, FIX), "tool_calls": []},
        {"content": block(ADMIN_OLD, ADMIN_FIX, "app/routes/admin.py"), "tool_calls": []},
        {"content": block(TRAV_OLD, TRAV_FIX, "app/routes/files.py"), "tool_calls": []},
    ])
    log = EventLog(tmp_path / "events.jsonl")
    summary = run_match(CFG, red, blue, log, rounds=3, work_root=tmp_path / "work",
                        out_dir=tmp_path / "out", base_port=9940, strategy="hybrid",
                        cache_path=tmp_path / "cache.json")
    assert summary.sweep_findings == 4 and summary.closed == 4
    assert red.calls == 0 and summary.tokens == 0 and summary.llm_calls == blue.calls == 4
