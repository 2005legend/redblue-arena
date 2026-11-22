import os

import httpx
import pytest

BASE = os.environ.get("ARENA_TARGET", "http://127.0.0.1:8000")


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE, timeout=10) as c:
        yield c


def login(client, user, pw):
    r = client.post("/api/login", json={"username": user, "password": pw})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["token"]}


def test_login_ok_and_bad(client):
    r = client.post("/api/login", json={"username": "alice", "password": "alice123"})
    assert r.status_code == 200 and "token" in r.json()
    r = client.post("/api/login", json={"username": "alice", "password": "nope"})
    assert r.status_code == 401


def test_search(client):
    r = client.get("/api/search", params={"q": "mug"})
    assert r.status_code == 200
    assert any("Mug" in p["name"] for p in r.json())


def test_list_and_view_own_order(client):
    h = login(client, "alice", "alice123")
    orders = client.get("/api/orders", headers=h).json()
    assert len(orders) >= 2
    r = client.get(f"/api/orders/{orders[0]['id']}", headers=h)
    assert r.status_code == 200 and r.json()["id"] == orders[0]["id"]


def test_create_order(client):
    h = login(client, "bob", "bob123")
    r = client.post("/api/orders", headers=h, json={"product_id": 1, "quantity": 2})
    assert r.status_code == 201 and r.json()["total"] == 17.0


def test_download_own_receipt(client):
    h = login(client, "alice", "alice123")
    r = client.get("/api/receipts/receipt_1001.txt", headers=h)
    assert r.status_code == 200 and "alice" in r.text


def test_admin_export_and_users(client):
    h = login(client, "admin", "admin123")
    r = client.get("/api/admin/export", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert len(data["users"]) >= 3 and len(data["orders"]) >= 4
    assert client.get("/api/admin/users", headers=h).status_code == 200
