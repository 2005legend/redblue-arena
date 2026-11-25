import os

import httpx

BASE = os.environ.get("ARENA_TARGET", "http://127.0.0.1:8000")


def token(user, pw):
    r = httpx.post(f"{BASE}/api/login", json={"username": user, "password": pw})
    assert r.status_code == 200
    return r.json()["token"]


def auth(user, pw):
    return {"Authorization": f"Bearer {token(user, pw)}"}


def test_login_ok():
    assert token("alice", "alice123").startswith("tok-")


def test_search_normal():
    r = httpx.get(f"{BASE}/api/search", params={"q": "coffee"})
    assert r.status_code == 200 and len(r.json()) >= 1


def test_own_invoice():
    r = httpx.get(f"{BASE}/api/invoices/1", headers=auth("alice", "alice123"))
    assert r.status_code == 200 and r.json()["id"] == 1


def test_list_own_invoices():
    r = httpx.get(f"{BASE}/api/invoices", headers=auth("alice", "alice123"))
    assert {i["id"] for i in r.json()} == {1, 2}


def test_admin_export_as_admin():
    r = httpx.get(f"{BASE}/api/admin/export", headers=auth("admin", "admin123"))
    assert r.status_code == 200


def test_download_public_file():
    r = httpx.get(f"{BASE}/api/files", params={"name": "welcome.txt"})
    assert r.status_code == 200 and "Welcome" in r.json()["content"]


def test_update_display_name():
    r = httpx.put(f"{BASE}/api/profile", json={"display_name": "Alice"},
                  headers=auth("alice", "alice123"))
    assert r.status_code == 200 and r.json()["user"]["display_name"] == "Alice"


def test_debug_config_as_admin():
    r = httpx.get(f"{BASE}/api/debug/config", headers=auth("admin", "admin123"))
    assert r.status_code == 200


def test_calc_expression():
    r = httpx.get(f"{BASE}/api/calc", params={"expr": "2*(3+4)"})
    assert r.status_code == 200 and r.json()["result"] == "14"
