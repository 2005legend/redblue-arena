import json
from pathlib import Path

from fastapi.testclient import TestClient

from arena import server, site_api

ROOT = Path(__file__).resolve().parent.parent


def test_replay_streams_sample_in_order(monkeypatch):
    monkeypatch.setattr(server, "MATCHES", ROOT / "matches")
    c = TestClient(server.app)
    with c.websocket_connect("/ws?replay=sample.jsonl&speed=1000") as ws:
        events = []
        while True:
            e = ws.receive_json()
            events.append(e)
            if e["type"] == "match_end":
                break
    types = [e["type"] for e in events]
    assert types[0] == "match_start" and types.count("breach") == 7 and types.count("patched") == 7
    assert events[0]["sample"] is True  # a replay is always labelled as a sample
    assert events[0]["strategy"] == "sweep"
    assert [e["seq"] for e in events] == list(range(len(events)))


def test_download_whitelist(monkeypatch):
    monkeypatch.setattr(server, "MATCHES", ROOT / "matches")
    c = TestClient(server.app)
    assert c.get("/api/export/sample/hardened.patch").status_code == 200
    assert c.get("/api/export/sample/security_tests.zip").status_code == 200
    assert c.get("/api/export/sample/arena.yaml").status_code == 404


def test_victim_page_is_served_with_its_attack_relay():
    c = TestClient(server.app)
    page = c.get("/target")
    assert page.status_code == 200
    assert "Live victim" in page.text
    # The relay was implemented on the storefront side only for a while, so guard both ends:
    # the victim page must post the request and the storefront must listen for it.
    assert "arena:replay" in page.text and "postMessage" in page.text
    shop = (ROOT / "fixtures/dev_target/app/routes/static/index.html").read_text(encoding="utf-8")
    assert "arena:replay" in shop


def test_target_live_sees_a_match_started_outside_serve(tmp_path, monkeypatch):
    """A CLI match never touches server.STATE; its log is the only place the target is announced."""
    match = tmp_path / "live-cli"
    match.mkdir()
    (match / "events.jsonl").write_text(
        json.dumps({"type": "target_live", "url": "http://127.0.0.1:8123", "port": 8123}) + "\n",
        encoding="utf-8")
    monkeypatch.setattr(server, "MATCHES", tmp_path)
    monkeypatch.setattr(server, "STATE", {"log": None, "match_id": None, "thread": None})
    monkeypatch.setattr(site_api, "_target_answers", lambda url, timeout=0.6: True)
    body = TestClient(server.app).get("/api/target/live").json()
    assert body == {"url": "http://127.0.0.1:8123", "port": 8123, "alive": True,
                    "match_id": "live-cli", "running": False}


def test_target_live_is_empty_when_nothing_is_listening(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "MATCHES", tmp_path)
    monkeypatch.setattr(server, "STATE", {"log": None, "match_id": None, "thread": None})
    body = TestClient(server.app).get("/api/target/live").json()
    assert body["alive"] is False and body["url"] is None
