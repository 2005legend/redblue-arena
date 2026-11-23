import os

import httpx

BASE = os.environ.get("ARENA_TARGET", "http://127.0.0.1:8000")


def test_admin_bypass_api_admin_export_does_not_leak_flag():
    headers = dict({'Authorization': 'Bearer tok-1'} or {})
    login = httpx.post(BASE + '/api/login', json={'username': 'alice', 'password': 'alice123'})
    token = next(v for k, v in login.json().items() if 'token' in k.lower())
    for key in headers:
        if key.lower() == 'authorization':
            headers[key] = headers[key].split(' ')[0] + ' ' + token
    r = httpx.request('GET', BASE + '/api/admin/export', headers=headers or None,
                      params=None, json=None)
    assert 'FLAG{admin_export_bypass}' not in r.text
