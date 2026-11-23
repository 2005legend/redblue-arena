"""Capture a functional test suite from the running app, then freeze it."""
import hashlib
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from arena.referee import run_functional_tests

SYSTEM = (
    "You write pytest tests for a web API from its OpenAPI spec. Tests describe NORMAL behaviour "
    "only: a user logging in, searching, reading and listing THEIR OWN data, and an admin using "
    "admin routes. Never test one user reading another user's data. Each test file reads the base "
    "URL from os.environ['ARENA_TARGET'] and uses httpx. Reply with files in this format, nothing else:\n"
    "### test_name.py\n```python\n(code)\n```"
)
FILE_RE = re.compile(r"###\s*(test_\w+\.py)\s*\n```(?:python)?\n(.*?)```", re.S)


@dataclass
class CaptureResult:
    kept: list = field(default_factory=list)
    dropped: list = field(default_factory=list)


def _uses_other_users_data(src: str, cfg) -> bool:
    other = cfg.sample_ids.get("other_invoice")
    return other is not None and re.search(rf"/invoices/{other}\b", src) is not None


def _admin_route_without_admin(src: str, cfg) -> bool:
    admin_users = [u["username"] for u in cfg.users if u.get("role") == "admin"]
    return any(r in src for r in cfg.admin_routes) and not any(u in src for u in admin_users)


def _digest(out_dir: Path) -> str:
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}"
             for p in sorted(out_dir.glob("test_*.py"))]
    return "\n".join(lines) + "\n"


def capture_tests(llm, openapi: dict, cfg, base_url: str, out_dir: Path) -> CaptureResult:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    reply = llm.chat([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": json.dumps({
            "openapi": openapi, "users": cfg.users, "sample_ids": cfg.sample_ids})},
    ])
    result = CaptureResult()
    probe = out_dir / "_probe"
    probe.mkdir(exist_ok=True)
    try:
        for name, src in FILE_RE.findall(reply.get("content") or ""):
            if _uses_other_users_data(src, cfg) or _admin_route_without_admin(src, cfg):
                result.dropped.append(name)
                continue
            (probe / name).write_text(src, encoding="utf-8")
            res = run_functional_tests(probe, base_url)
            if res.failed == 0 and res.passed > 0:
                (out_dir / name).write_text(src, encoding="utf-8")
                result.kept.append(name)
            else:
                result.dropped.append(name)
            (probe / name).unlink()
    finally:
        shutil.rmtree(probe, ignore_errors=True)  # pytest leaves __pycache__ in the probe dir
    (out_dir / "FROZEN.sha256").write_text(_digest(out_dir))
    return result


def verify_frozen(out_dir: Path) -> bool:
    out_dir = Path(out_dir)
    return (out_dir / "FROZEN.sha256").read_text() == _digest(out_dir)


def review_tests(out_dir: Path, ask=input) -> list:
    """Human approval step: returns the files the user rejected (and removes them)."""
    rejected = []
    for p in sorted(Path(out_dir).glob("test_*.py")):
        print(f"\n--- {p.name} ---\n{p.read_text()}")
        if ask(f"Keep {p.name}? [Y/n] ").strip().lower() == "n":
            p.unlink()
            rejected.append(p.name)
    (Path(out_dir) / "FROZEN.sha256").write_text(_digest(Path(out_dir)))
    return rejected
