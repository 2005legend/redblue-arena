"""Deterministic referee: no LLM decides who wins."""
import re
from dataclasses import dataclass

from arena.httptool import HttpResult, send_request

FLAG_RE = re.compile(r"FLAG\{[A-Za-z0-9_]+\}")


@dataclass
class Exploit:
    method: str
    path: str
    headers: dict | None
    params: dict | None
    json: dict | None
    flag: str
    vuln_class: str


def find_flags(text: str) -> list[str]:
    return FLAG_RE.findall(text or "")


def replay(exploit: Exploit, base_url: str) -> HttpResult:
    return send_request(exploit.method, base_url + exploit.path, headers=exploit.headers,
                        params=exploit.params, json=exploit.json)
