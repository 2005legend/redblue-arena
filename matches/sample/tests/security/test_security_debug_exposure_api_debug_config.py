import os

import httpx

BASE = os.environ.get("ARENA_TARGET", "http://127.0.0.1:8000")


def test_debug_exposure_api_debug_config_does_not_leak_flag():
    headers = dict(None or {})
    r = httpx.request('GET', BASE + '/api/debug/config', headers=headers or None,
                      params=None, json=None)
    assert 'FLAG{debug_config_leak}' not in r.text
