import os

import httpx

BASE = os.environ.get("ARENA_TARGET", "http://127.0.0.1:8000")


def test_path_traversal_api_files_does_not_leak_flag():
    r = httpx.request('GET', BASE + '/api/files', headers=None,
                      params={'name': '../secret.txt'}, json=None)
    assert 'FLAG{path_traversal_leak}' not in r.text
