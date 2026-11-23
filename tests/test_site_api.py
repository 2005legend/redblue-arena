import shutil
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
    assert b["red_flags_captured"] == 4 and b["blue_patches_approved"] == 4
    assert b["simulation_mode"] == "sweep"
    assert b["replay"] == "sample.jsonl"
    assert b["outcome"].startswith("BLUE VICTORY")
    assert client.get(f"/api/battles/{b['id']}").json()["id"] == "sample"
    assert client.get("/api/battles/nope").status_code == 404


def test_dashboard_counts_match_the_log(client):
    stats = client.get("/api/dashboard/stats").json()
    assert stats["total_battles"] == 1
    assert stats["vulnerabilities_discovered"] == 4
    assert stats["vulnerabilities_patched"] == 4
    assert stats["blue_defense_rate"] == 100.0
    comparison = {r["metric"]: r for r in stats["charts"]["comparison"]}
    assert comparison["SQL Injection (SQLi)"]["red"] == 1
    assert comparison["SQL Injection (SQLi)"]["blue"] == 1
    assert len(stats["recent_battles"]) == 1


def test_vulnerabilities_show_the_real_packet_and_diff(client):
    rows = client.get("/api/vulnerabilities").json()
    assert len(rows) == 4
    sqli = next(r for r in rows if r["affected_endpoint"] == "GET /api/search")
    assert "' OR 1=1--" in sqli["detection_evidence"]
    assert "SELECT id, name FROM products" in sqli["root_cause"]
    assert "LIKE ?" in sqli["mitigation"]
    assert sqli["patched"] is True and sqli["match_id"] == "sample"
    i = site_api.VULN_META["sqli"]
    assert sqli["severity"] == i["severity"] and sqli["cwe"] == i["cwe"]


def test_patches_carry_real_diffs(client):
    rows = client.get("/api/patches").json()
    assert len(rows) == 4
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
        "FLAG{admin_export_bypass}", "FLAG{path_traversal_leak}"}
    assert client.get("/api/battles/nope/report").status_code == 404


def test_target_status_reports_the_real_config_and_refuses_controls(client):
    status = client.get("/api/target/config/status").json()
    assert status["app_dir"].replace("\\", "/").endswith("fixtures/dev_target")
    assert "/api/admin/export" in status["admin_routes"]
    assert status["flag_owners"]["FLAG{idor_invoice_leak}"] == "bob"
    assert status["global_mode"] == "secure"  # the sample patched all four classes
    assert status["patches"]["admin_auth"] is True
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
