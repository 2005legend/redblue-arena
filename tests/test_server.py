from pathlib import Path

from fastapi.testclient import TestClient

from arena import server

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
    assert types[0] == "match_start" and types.count("breach") == 4 and types.count("patched") == 4
    assert events[0]["sample"] is True  # a replay is always labelled as a sample
    assert events[0]["strategy"] == "sweep"
    assert [e["seq"] for e in events] == list(range(len(events)))


def test_download_whitelist(monkeypatch):
    monkeypatch.setattr(server, "MATCHES", ROOT / "matches")
    c = TestClient(server.app)
    assert c.get("/api/export/sample/hardened.patch").status_code == 200
    assert c.get("/api/export/sample/security_tests.zip").status_code == 200
    assert c.get("/api/export/sample/arena.yaml").status_code == 404
