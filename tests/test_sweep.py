from pathlib import Path

import httpx

from arena.config import attacker_accounts, load_config
from arena.discover import find_login_path, routes
from arena.sandbox import PortAllocator, TargetProcess
from arena.sweep import Sweep, should_run_llm

ROOT = Path(__file__).resolve().parent.parent
CFG = load_config(str(ROOT / "arena.yaml"))
ATTACKER = attacker_accounts(CFG)

OPENAPI = {
    "paths": {
        "/api/login": {"post": {"requestBody": {"content": {"application/json": {"schema": {
            "$ref": "#/components/schemas/Login"}}}}}},
        "/api/invoices/{invoice_id}": {"get": {"parameters": [
            {"name": "invoice_id", "in": "path", "required": True,
             "schema": {"type": "integer"}}]}},
        "/api/files": {"get": {"parameters": [
            {"name": "name", "in": "query", "required": True, "schema": {"type": "string"}}]}},
    },
    "components": {"schemas": {"Login": {"properties": {"username": {}, "password": {}}}}},
}


def target(tmp_path, start):
    t = TargetProcess(CFG.app_dir, CFG.seed_db, PortAllocator(start).next(), tmp_path,
                      extra_paths=CFG.extra_paths)
    t.prepare()
    t.start()
    return t


def test_discover_reads_paths_params_and_login():
    table = routes(OPENAPI)
    invoice = next(r for r in table if r.path == "/api/invoices/{invoice_id}")
    assert invoice.method == "GET" and invoice.path_params()[0].type == "integer"
    assert [p.name for p in next(r for r in table if r.path == "/api/files").query_params()] == ["name"]
    assert find_login_path(OPENAPI) == "/api/login"
    assert find_login_path(OPENAPI, override="/custom/login") == "/custom/login"


def test_sweep_finds_all_four_classes_without_an_llm(tmp_path):
    t = target(tmp_path, 9400)
    events = []
    try:
        openapi = httpx.get(t.url + "/openapi.json").json()
        sweep = Sweep(t.url, openapi, ATTACKER, flag_owners=CFG.flag_owners,
                      admin_routes=CFG.admin_routes, login_path=CFG.login_path,
                      loot_paths=CFG.loot_paths, emit=events.append)
        exploits = sweep.run()
    finally:
        t.stop()
    by_flag = {e.flag: e.vuln_class for e in exploits}
    assert by_flag == {
        "FLAG{sqli_leaked_db}": "sqli",
        "FLAG{idor_invoice_leak}": "idor",
        "FLAG{admin_export_bypass}": "admin_bypass",
        "FLAG{path_traversal_leak}": "path_traversal",
    }
    idor = next(e for e in exploits if e.vuln_class == "idor")
    assert idor.path == "/api/invoices/3"
    assert idor.login == {"path": "/api/login",
                          "json": {"username": "alice", "password": "alice123"}}
    assert all(e["source"] == "sweep" for e in events if e["type"] in ("red_action", "breach"))
    breaches = {e["vuln_class"]: e for e in events if e["type"] == "breach"}
    assert breaches["sqli"]["method"] == "GET"
    assert breaches["sqli"]["params"] == {"q": "' OR 1=1--"}
    assert breaches["path_traversal"]["params"] == {"name": "../secret.txt"}
    assert sweep.requests <= 40


def test_sweep_never_counts_the_owner_reading_their_own_flag(tmp_path):
    t = target(tmp_path, 9410)
    bob = [u for u in CFG.users if u["username"] == "bob"]
    try:
        openapi = httpx.get(t.url + "/openapi.json").json()
        exploits = Sweep(t.url, openapi, bob, flag_owners=CFG.flag_owners,
                         admin_routes=CFG.admin_routes, loot_paths=CFG.loot_paths).run()
    finally:
        t.stop()
    assert "FLAG{idor_invoice_leak}" not in {e.flag for e in exploits}
    assert "admin_bypass" in {e.vuln_class for e in exploits}


def test_should_run_llm_only_for_leftovers():
    assert should_run_llm("hybrid", []) is True
    assert should_run_llm("hybrid", ["FLAG{x}"]) is False
    assert should_run_llm("hybrid", ["FLAG{x}"], explore=True) is True
    assert should_run_llm("sweep", []) is False
    assert should_run_llm("llm", ["FLAG{x}"]) is True
