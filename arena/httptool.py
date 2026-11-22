"""The only way Red may send traffic. Locked to sandbox targets in code."""
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from arena import sandbox


class HostLockError(Exception):
    pass


@dataclass
class HttpResult:
    status: int
    headers: dict
    body: str
    elapsed_ms: int


def send_request(method: str, url: str, headers: dict | None = None, params: dict | None = None,
                 json: dict | None = None) -> HttpResult:
    parsed = urlparse(url)
    if parsed.hostname not in ("127.0.0.1", "localhost"):
        raise HostLockError(f"host {parsed.hostname!r} is not allowed")
    if parsed.port not in sandbox.ALLOWED_PORTS:
        raise HostLockError(f"port {parsed.port!r} is not a registered sandbox target")
    start = time.time()
    r = httpx.request(method.upper(), url, headers=headers, params=params, json=json, timeout=10)
    return HttpResult(r.status_code, dict(r.headers), r.text[:4000],
                      int((time.time() - start) * 1000))
