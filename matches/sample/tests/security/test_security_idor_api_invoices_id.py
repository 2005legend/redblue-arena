import os

import httpx

BASE = os.environ.get("ARENA_TARGET", "http://127.0.0.1:8000")


def test_idor_api_invoices_id_does_not_leak_flag():
    headers = dict({'Authorization': 'Bearer tok-1'} or {})
    login = httpx.post(BASE + '/api/login', json={'username': 'alice', 'password': 'alice123'})
    token = next(v for k, v in login.json().items() if 'token' in k.lower())
    for key in headers:
        if key.lower() == 'authorization':
            headers[key] = headers[key].split(' ')[0] + ' ' + token
    r = httpx.request('GET', BASE + '/api/invoices/3', headers=headers or None,
                      params=None, json=None)
    assert 'FLAG{idor_invoice_leak}' not in r.text
