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
    login: dict | None = None  # {'path', 'json'}: how the attacker got its token


def find_flags(text: str) -> list[str]:
    return FLAG_RE.findall(text or "")


def find_token(text: str) -> str | None:
    """Pull a session token out of a login response body (any JSON key containing 'token')."""
    import json as _json
    try:
        data = _json.loads(text)
    except (ValueError, TypeError):
        return None
    if isinstance(data, dict):
        for key, value in data.items():
            if "token" in key.lower() and isinstance(value, str):
                return value
    return None


def replay(exploit: Exploit, base_url: str) -> HttpResult:
    """Repeat the exploit as the same attacker. If it came with a login, log in again first, so a
    patch cannot 'win' just by invalidating the old token (e.g. by keeping sessions in memory)."""
    headers = dict(exploit.headers or {})
    if exploit.login:
        res = send_request("POST", base_url + exploit.login["path"], json=exploit.login["json"])
        token = find_token(res.body)
        if token:
            for key, value in list(headers.items()):
                if key.lower() == "authorization":
                    headers[key] = value.split(" ")[0] + " " + token if " " in value else token
    return send_request(exploit.method, base_url + exploit.path, headers=headers or None,
                        params=exploit.params, json=exploit.json)


@dataclass
class TestResult:
    __test__ = False  # not a pytest class
    passed: int
    failed: int
    output: str


@dataclass
class Verdict:
    ok: bool
    tests: TestResult
    replay_flag_found: bool


def run_functional_tests(tests_dir, base_url: str) -> TestResult:
    import os
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests_dir), "-q", "--tb=short", "-p", "no:cacheprovider"],
        env=dict(os.environ, ARENA_TARGET=base_url), capture_output=True, text=True, timeout=120)
    out = proc.stdout + proc.stderr
    passed = re.search(r"(\d+) passed", out)
    failed = re.search(r"(\d+) failed", out)
    errors = re.search(r"(\d+) error", out)
    n_failed = int(failed.group(1)) if failed else 0
    if errors or (proc.returncode != 0 and not failed):
        n_failed += int(errors.group(1)) if errors else 1
    return TestResult(int(passed.group(1)) if passed else 0, n_failed, out[-3000:])


def verify_patch(staging, exploit: Exploit, tests_dir) -> Verdict:
    """Blue scores only if every frozen test passes AND the exploit replay no longer leaks."""
    tests = run_functional_tests(tests_dir, staging.url)
    found = exploit.flag in find_flags(replay(exploit, staging.url).body)
    return Verdict(ok=tests.failed == 0 and tests.passed > 0 and not found,
                   tests=tests, replay_flag_found=found)
