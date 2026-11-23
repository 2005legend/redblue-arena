import os

import httpx

BASE = os.environ.get("ARENA_TARGET", "http://127.0.0.1:8000")


def test_sqli_api_search_does_not_leak_flag():
    headers = dict(None or {})
    r = httpx.request('GET', BASE + '/api/search', headers=headers or None,
                      params={'q': "' OR 1=1--"}, json=None)
    assert 'FLAG{sqli_leaked_db}' not in r.text
