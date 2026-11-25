import os

import httpx

BASE = os.environ.get("ARENA_TARGET", "http://127.0.0.1:8000")


def test_code_injection_api_calc_does_not_leak_flag():
    headers = dict(None or {})
    r = httpx.request('GET', BASE + '/api/calc', headers=headers or None,
                      params={'expr': "[v for v in globals().values() if 'FLAG{' in str(v)]"}, json=None)
    assert 'FLAG{code_injection_leak}' not in r.text
