import json
import os
import shutil
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from arena import server, site_api

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def client(tmp_path, monkeypatch):
    shutil.copy(ROOT / "matches" / "sample.jsonl", tmp_path / "sample.jsonl")
    monkeypatch.setattr(server, "MATCHES", tmp_path)
    monkeypatch.setattr(server, "CONFIG", str(ROOT / "arena.yaml"))
    return TestClient(server.app)


def test_battles_are_derived_from_the_event_log(client):
    rows = client.get("/api/battles").json()
    assert len(rows) == 1
    b = rows[0]
    assert b["id"] == "sample" and b["status"] == "completed"
    assert b["red_flags_captured"] == 7 and b["blue_patches_approved"] == 7
    assert b["simulation_mode"] == "sweep"
    assert b["replay"] == "sample.jsonl"
    assert b["outcome"].startswith("BLUE VICTORY")
    # Tier-1 proof straight from the log: no model was called and every fix came from the cache.
    assert b["llm_calls"] == 0 and b["tokens_used"] == 0
    assert b["red_llm_calls"] == 0 and b["blue_llm_calls"] == 0
    assert b["red_tokens"] == 0 and b["blue_tokens"] == 0
    assert b["sweep_requests"] == 25 and b["sweep_findings"] == 7
    assert b["cache_hits"] == 7
    assert client.get(f"/api/battles/{b['id']}").json()["id"] == "sample"
    assert client.get("/api/battles/nope").status_code == 404


def test_dashboard_counts_match_the_log(client):
    stats = client.get("/api/dashboard/stats").json()
    assert stats["total_battles"] == 1
    assert stats["vulnerabilities_discovered"] == 7
    assert stats["vulnerabilities_patched"] == 7
    assert stats["blue_defense_rate"] == 100.0
    comparison = {r["metric"]: r for r in stats["charts"]["comparison"]}
    assert comparison["SQL Injection (SQLi)"]["red"] == 1
    assert comparison["SQL Injection (SQLi)"]["blue"] == 1
    assert len(stats["recent_battles"]) == 1


def test_vulnerabilities_show_the_real_packet_and_diff(client):
    rows = client.get("/api/vulnerabilities").json()
    assert len(rows) == 7
    sqli = next(r for r in rows if r["affected_endpoint"] == "GET /api/search")
    assert "' OR 1=1--" in sqli["detection_evidence"]
    assert "SELECT id, name FROM products" in sqli["root_cause"]
    assert "LIKE ?" in sqli["mitigation"]
    assert sqli["patched"] is True and sqli["match_id"] == "sample"
    i = site_api.VULN_META["sqli"]
    assert sqli["severity"] == i["severity"] and sqli["cwe"] == i["cwe"]
    mass = next(r for r in rows if r["affected_endpoint"] == "PUT /api/profile")
    assert '"role": "admin"' in mass["detection_evidence"]
    debug = next(r for r in rows if r["affected_endpoint"] == "GET /api/debug/config")
    assert debug["severity"] == "HIGH"
    calc = next(r for r in rows if r["affected_endpoint"] == "GET /api/calc")
    assert "eval" in calc["root_cause"] or "eval" in calc["mitigation"]


def test_patches_carry_real_diffs(client):
    rows = client.get("/api/patches").json()
    assert len(rows) == 7
    for p in rows:
        assert p["source_file"].startswith("app/routes/")
        assert p["status"] == "approved"
        assert "+++ b/app/" in p["diff_code"]
        assert p["original_code"] and p["proposed_patch"]
        assert "Patch verified in" in p["referee_notes"]


def test_report_marks_every_finding_mitigated(client):
    rep = client.get("/api/battles/sample/report").json()
    assert rep["battle"]["id"] == "sample"
    assert {f["status"] for f in rep["findings"]} == {"Mitigated"}
    assert {f["canary_token"] for f in rep["findings"]} == {
        "FLAG{sqli_leaked_db}", "FLAG{idor_invoice_leak}",
        "FLAG{admin_export_bypass}", "FLAG{path_traversal_leak}",
        "FLAG{mass_assignment_leak}", "FLAG{debug_config_leak}",
        "FLAG{code_injection_leak}"}
    assert client.get("/api/battles/nope/report").status_code == 404


def test_target_status_reports_the_real_config_and_refuses_controls(client):
    status = client.get("/api/target/config/status").json()
    assert status["app_dir"].replace("\\", "/").endswith("fixtures/dev_target")
    assert "/api/admin/export" in status["admin_routes"]
    assert status["flag_owners"]["FLAG{idor_invoice_leak}"] == "bob"
    assert status["global_mode"] == "secure"  # the sample patched all seven classes
    assert status["patches"]["admin_auth"] is True
    assert status["patches"]["mass_assignment"] is True
    assert status["patches"]["debug_exposure"] is True
    assert status["patches"]["code_injection"] is True
    assert "sandbox" in status["note"]

    assert client.post("/api/battles/sample/start").status_code == 409
    r = client.post("/api/target/exploit/run", json={"payload": "x"})
    assert r.status_code == 503 and "sandbox" in r.json()["detail"]


def test_no_matches_yields_empty_but_valid_views(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "MATCHES", tmp_path)
    c = TestClient(server.app)
    assert c.get("/api/battles").json() == []
    assert c.get("/api/vulnerabilities").json() == []
    assert c.get("/api/patches").json() == []
    stats = c.get("/api/dashboard/stats").json()
    assert stats["total_battles"] == 0 and stats["recent_battles"] == []


def test_live_match_dirs_use_their_own_id_and_duplicate_event_copies_are_skipped(tmp_path):
    shutil.copy(ROOT / "matches" / "sample.jsonl", tmp_path / "sample.jsonl")
    (tmp_path / "sample").mkdir()
    shutil.copy(ROOT / "matches" / "sample.jsonl", tmp_path / "sample" / "events.jsonl")
    (tmp_path / "live-1").mkdir()
    shutil.copy(ROOT / "matches" / "sample.jsonl", tmp_path / "live-1" / "events.jsonl")
    rows = site_api.list_matches(tmp_path)
    ids = sorted(r["id"] for r in rows)
    assert ids == ["live-1", "sample"]  # the sample/events.jsonl copy is not a second battle


def test_an_abandoned_log_without_match_end_is_interrupted_not_running(tmp_path):
    import json as _json
    import os as _os
    live = tmp_path / "live-dead"
    live.mkdir()
    log = live / "events.jsonl"
    log.write_text(_json.dumps({"type": "match_start", "strategy": "hybrid", "seq": 1, "ts": 0}) + "\n",
                   encoding="utf-8")
    old = 1_700_000_000
    _os.utime(log, (old, old))
    row = site_api.summarize(log)
    assert row["status"] == "interrupted"
    assert row["outcome"].startswith("MATCH INTERRUPTED")


def test_duplicate_breach_events_do_not_flip_the_referee_verdict(tmp_path):
    import json as _json
    live = tmp_path / "live-explore"
    live.mkdir()
    log = live / "events.jsonl"
    bugs = [("sqli", "/api/search"), ("idor", "/api/invoices/{id}"),
            ("admin_bypass", "/api/admin/export"), ("path_traversal", "/api/files")]
    lines = [{"type": "match_start", "strategy": "hybrid", "seq": 1, "ts": 0}]
    # The sweep finds four bugs, then Red's LLM re-tests one before Blue patches anything.
    for i, (cls, route) in enumerate(bugs + [bugs[0]]):
        lines.append({"type": "breach", "vuln_class": cls, "route": route,
                      "flag": f"FLAG{{{cls}}}", "seq": 2 + i, "ts": i})
    for i, (cls, route) in enumerate(bugs):
        lines.append({"type": "patched", "vuln_class": cls, "route": route, "seq": 10 + i, "ts": 10 + i})
    lines.append({"type": "match_end", "summary": {"red": 4, "blue": 4, "closed": 4, "total": 4},
                  "seq": 20, "ts": 20})
    log.write_text("".join(_json.dumps(e) + "\n" for e in lines), encoding="utf-8")
    row = site_api.summarize(log)
    assert row["outcome"].startswith("BLUE VICTORY")
    assert row["red_discoveries"] == 4
    assert row["description"].startswith("4 canary findings")
    stats = site_api.dashboard(tmp_path)
    assert stats["vulnerabilities_discovered"] == 4
    assert stats["blue_defense_rate"] == 100.0
    comparison = {r["metric"]: r for r in stats["charts"]["comparison"]}
    assert comparison["SQL Injection (SQLi)"]["red"] == 1  # re-test counted once


def test_agent_usage_is_split_per_side_with_inference_for_old_logs(tmp_path):
    import json as _json

    def write(name, summary, thinking=0):
        d = tmp_path / name
        d.mkdir()
        lines = [{"type": "match_start", "strategy": "hybrid", "seq": 1, "ts": 0}]
        seq = 2
        for _ in range(thinking):
            lines.append({"type": "blue_thinking", "text": "x", "seq": seq, "ts": seq})
            seq += 1
        lines.append({"type": "match_end", "summary": summary, "seq": seq, "ts": seq})
        path = d / "events.jsonl"
        path.write_text("".join(_json.dumps(e) + "\n" for e in lines), encoding="utf-8")
        return site_api.summarize(path)

    new = write("live-new", {"red": 4, "blue": 4, "closed": 4, "total": 4, "tokens": 4200,
                             "llm_calls": 6, "red_llm_calls": 2, "blue_llm_calls": 4,
                             "red_tokens": 1200, "blue_tokens": 3000})
    assert (new["red_llm_calls"], new["blue_llm_calls"]) == (2, 4)
    assert (new["red_tokens"], new["blue_tokens"]) == (1200, 3000)

    # Old log, Blue-only run: each blue_thinking is one model call; Red made none, so it owns no tokens.
    blue_only = write("live-cold", {"red": 4, "blue": 4, "closed": 4, "total": 4,
                                    "tokens": 3964, "llm_calls": 4}, thinking=4)
    assert (blue_only["red_llm_calls"], blue_only["blue_llm_calls"]) == (0, 4)
    assert (blue_only["red_tokens"], blue_only["blue_tokens"]) == (0, 3964)

    # Old log, Red-only run (explore over cached fixes): all calls and tokens are Red's.
    red_only = write("live-explore", {"red": 4, "blue": 4, "closed": 4, "total": 4,
                                      "tokens": 54972, "llm_calls": 33})
    assert (red_only["red_llm_calls"], red_only["blue_llm_calls"]) == (33, 0)
    assert (red_only["red_tokens"], red_only["blue_tokens"]) == (54972, 0)

    # Both sides called and the split was not recorded: calls are provable, tokens are not.
    mixed = write("live-mixed", {"red": 4, "blue": 4, "closed": 4, "total": 4,
                                 "tokens": 1000, "llm_calls": 5}, thinking=2)
    assert (mixed["red_llm_calls"], mixed["blue_llm_calls"]) == (3, 2)
    assert mixed["red_tokens"] is None and mixed["blue_tokens"] is None


def _live_match(tmp_path, name, events, mtime):
    d = tmp_path / name
    d.mkdir(parents=True)
    log = d / "events.jsonl"
    log.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    os.utime(log, (mtime, mtime))
    return d


def test_live_target_follows_the_last_target_live_event(tmp_path):
    _live_match(tmp_path, "live-1", [
        {"type": "target_live", "url": "http://127.0.0.1:8001", "port": 8001, "ts": 1},
        {"type": "target_live", "url": "http://127.0.0.1:8002", "port": 8002, "ts": 2},
        {"type": "patched", "vuln_class": "sqli", "ts": 3},
    ], time.time())
    found = site_api.live_target(tmp_path, check=lambda url, timeout: True)
    assert found == {"url": "http://127.0.0.1:8002", "port": 8002, "alive": True,
                     "match_id": "live-1"}
    # The newer target replaced the old one, so the old port must not be reported.
    assert found["port"] != 8001


def test_live_target_is_dead_after_target_down_or_a_failed_health_check(tmp_path):
    _live_match(tmp_path, "live-1", [
        {"type": "target_live", "url": "http://127.0.0.1:8001", "port": 8001, "ts": 1},
        {"type": "target_down", "port": 8001, "ts": 2},
    ], time.time())
    assert site_api.live_target(tmp_path, check=lambda url, timeout: True)["alive"] is False

    _live_match(tmp_path, "live-2", [
        {"type": "target_live", "url": "http://127.0.0.1:8003", "port": 8003, "ts": 1},
    ], time.time() + 1)
    dead = site_api.live_target(tmp_path, check=lambda url, timeout: False)
    assert dead == {"url": None, "port": 8003, "alive": False, "match_id": "live-2"}


def test_live_target_prefers_the_newest_match_and_never_revives_an_old_one(tmp_path):
    now = time.time()
    _live_match(tmp_path, "live-old", [
        {"type": "target_live", "url": "http://127.0.0.1:8001", "port": 8001, "ts": 1},
    ], now - 100)
    _live_match(tmp_path, "live-new", [
        {"type": "target_live", "url": "http://127.0.0.1:8009", "port": 8009, "ts": 1},
        {"type": "target_down", "port": 8009, "ts": 2},
    ], now)
    # The newest run tore its target down, so an older kept target must not come back as live.
    found = site_api.live_target(tmp_path, check=lambda url, timeout: True)
    assert found["alive"] is False and found["match_id"] == "live-new"
    # A CLI match is only visible because its log is scanned; asking for it by id works too.
    assert site_api.live_target(tmp_path, "live-old", check=lambda url, timeout: True)["alive"] is True
    assert site_api.live_target(tmp_path, "nope") == {"url": None, "port": None,
                                                      "alive": False, "match_id": "nope"}


def test_live_target_finds_nothing_in_a_recording_only_tree(tmp_path):
    shutil.copy(ROOT / "matches" / "sample.jsonl", tmp_path / "sample.jsonl")
    assert site_api.live_target(tmp_path)["alive"] is False
