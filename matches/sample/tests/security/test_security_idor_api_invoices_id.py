import os

import httpx

BASE = os.environ.get("ARENA_TARGET", "http://127.0.0.1:8000")


def test_idor_api_invoices_id_does_not_leak_flag():
    r = httpx.request('GET', BASE + '/api/invoices/3', headers={'Authorization': 'Bearer tok-1'},
                      params=None, json=None)
    assert 'FLAG{idor_invoice_leak}' not in r.text
