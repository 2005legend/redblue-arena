import os

import httpx

BASE = os.environ.get("ARENA_TARGET", "http://127.0.0.1:8000")


def test_admin_bypass_api_admin_export_does_not_leak_flag():
    r = httpx.request('GET', BASE + '/api/admin/export', headers={'Authorization': 'Bearer tok-1'},
                      params=None, json=None)
    assert 'FLAG{admin_export_bypass}' not in r.text
