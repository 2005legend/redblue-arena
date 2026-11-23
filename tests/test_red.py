from pathlib import Path

import httpx
import pytest

from arena.config import load_config
from arena.llm import BudgetExceeded
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
    assert breach[0]["method"] == "GET" and breach[0]["path"] == "/api/invoices/3"


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


def test_red_survives_non_object_tool_args(tmp_path):
    t = target(tmp_path, PortAllocator(9615).next())
    events = []
    try:
        llm = FakeLLM([
            tc("send_http_request", None, raw="[]"),
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


def test_red_records_login_so_replay_can_repeat_it(tmp_path):
    t = target(tmp_path, PortAllocator(9620).next())
    try:
        llm = FakeLLM([
            tc("send_http_request", {"method": "POST", "path": "/api/login",
                                     "json": {"username": "alice", "password": "alice123"}}),
            tc("send_http_request", {"method": "GET", "path": "/api/invoices/3",
                                     "headers": {"Authorization": "Bearer tok-1"}}),
        ])
        exploits = run_red(llm, t.url, {"paths": {}}, USERS, lambda e: None, max_steps=10)
    finally:
        t.stop()
    assert exploits[0].login == {"path": "/api/login",
                                 "json": {"username": "alice", "password": "alice123"}}


def test_reading_your_own_data_is_not_a_breach(tmp_path):
    t = target(tmp_path, PortAllocator(9630).next())
    try:
        llm = FakeLLM([
            tc("send_http_request", {"method": "POST", "path": "/api/login",
                                     "json": {"username": "bob", "password": "bob123"}}),
            tc("send_http_request", {"method": "GET", "path": "/api/invoices/3",
                                     "headers": {"Authorization": "Bearer tok-2"}}),
        ])
        exploits = run_red(llm, t.url, {"paths": {}}, USERS, lambda e: None, max_steps=10,
                           flag_owners={"FLAG{idor_invoice_leak}": "bob"})
    finally:
        t.stop()
    assert exploits == []


def test_budget_exhaustion_is_not_swallowed():
    llm = FakeLLM([BudgetExceeded("token budget 5 exhausted")])
    with pytest.raises(BudgetExceeded):
        run_red(llm, "http://127.0.0.1:1", {"paths": {}}, USERS, lambda e: None)


def test_red_returns_what_it_found_when_the_llm_gives_out(tmp_path):
    t = target(tmp_path, PortAllocator(9640).next())
    events = []
    try:
        llm = FakeLLM([
            tc("send_http_request", {"method": "GET", "path": "/api/search", "params": {"q": "' OR 1=1--"}}),
            RuntimeError("all models failed: rate limited"),
        ])
        exploits = run_red(llm, t.url, {"paths": {}}, USERS, events.append, max_steps=10)
    finally:
        t.stop()
    assert [e.vuln_class for e in exploits] == ["sqli"]
    assert any(e["type"] == "red_error" and "all models failed" in e["error"] for e in events)


def test_red_logs_in_before_asking_the_model(tmp_path):
    t = target(tmp_path, PortAllocator(9650).next())
    events = []
    try:
        openapi = httpx.get(t.url + "/openapi.json").json()
        llm = FakeLLM([tc("discover_routes", {})])
        run_red(llm, t.url, openapi, USERS, events.append, max_steps=5)
    finally:
        t.stop()
    intro = llm.seen[0][1]["content"]
    assert "already logged in as alice" in intro and "Bearer tok-1" in intro
    assert any(e["type"] == "red_action" and e["tool"] == "prelogin" for e in events)


def test_red_observations_are_short_and_highlight_flags(tmp_path):
    t = target(tmp_path, PortAllocator(9660).next())
    try:
        openapi = {"paths": {}}
        llm = FakeLLM([
            tc("send_http_request", {"method": "GET", "path": "/api/invoices/3",
                                     "headers": {"Authorization": "Bearer tok-1"}}),
        ])
        run_red(llm, t.url, openapi, USERS, lambda e: None, max_steps=3)
    finally:
        t.stop()
    tool_message = llm.seen[1][-1]
    assert tool_message["role"] == "tool"
    assert "FLAGS FOUND: FLAG{idor_invoice_leak}" in tool_message["content"]


def test_red_old_history_is_dropped_but_tool_pairs_stay_together(tmp_path):
    llm = FakeLLM([tc("discover_routes", {}, id=f"t{i}") for i in range(4)])
    run_red(llm, "http://127.0.0.1:1", {"paths": {}}, USERS, lambda e: None, max_steps=6,
            keep_steps=2)
    last = llm.seen[-1]
    assert len(last) == 2 + 2 * 2
    assert [m["role"] for m in last[2:]] == ["assistant", "tool", "assistant", "tool"]
