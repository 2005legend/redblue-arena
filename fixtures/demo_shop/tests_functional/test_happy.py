"""Frozen happy paths for the Lumen Goods demo target. ARENA_TARGET is set by the arena;
these tests must keep passing after every accepted patch."""
import os

import httpx

BASE = os.environ["ARENA_TARGET"]


def login(username, password):
    r = httpx.post(BASE + "/api/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def test_login_ok():
    body = login("alice", "alice123")
    assert body["token"] and body["role"] == "user"


def test_public_product_list():
    r = httpx.get(BASE + "/api/products/list")
    assert r.status_code == 200 and len(r.json()["products"]) >= 4


def test_search_finds_a_product():
    r = httpx.get(BASE + "/api/products/search", params={"q": "grinder"})
    assert r.status_code == 200 and len(r.json()["results"]) >= 1


def test_own_order_readable():
    t = login("alice", "alice123")["token"]
    r = httpx.get(BASE + "/api/orders/1", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200 and r.json()["user_id"] == 1


def test_list_own_orders():
    t = login("alice", "alice123")["token"]
    r = httpx.get(BASE + "/api/orders", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    assert {o["id"] for o in r.json()["orders"]} == {1}


def test_list_own_tickets():
    t = login("alice", "alice123")["token"]
    r = httpx.get(BASE + "/api/support/tickets", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    assert {tk["id"] for tk in r.json()["tickets"]} == {2}


def test_admin_export_as_admin():
    t = login("admin", "admin123")["token"]
    r = httpx.get(BASE + "/api/admin/export", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200 and r.json()["users"]


def test_admin_customers_as_admin():
    t = login("admin", "admin123")["token"]
    r = httpx.get(BASE + "/api/admin/customers", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200 and r.json()["customers"]


def test_profile_display_name_role_unchanged():
    t = login("alice", "alice123")["token"]
    r = httpx.put(BASE + "/api/account", headers={"Authorization": f"Bearer {t}"},
                  json={"display_name": "Alice A."})
    assert r.status_code == 200 and r.json()["role"] == "user"


def test_settings_theme_change():
    t = login("alice", "alice123")["token"]
    r = httpx.patch(BASE + "/api/account/settings", headers={"Authorization": f"Bearer {t}"},
                    json={"theme": "dark"})
    assert r.status_code == 200 and r.json()["role"] == "user"


def test_download_normal_file():
    r = httpx.get(BASE + "/api/downloads", params={"file": "welcome.txt"})
    assert r.status_code == 200 and "welcome" in r.text.lower()


def test_attachment_normal_file():
    r = httpx.get(BASE + "/api/attachments", params={"name": "manual.txt"})
    assert r.status_code == 200 and "manual" in r.text.lower()
