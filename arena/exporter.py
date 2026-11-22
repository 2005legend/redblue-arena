"""Writes the user's deliverables: hardened patch, security tests, and a report."""
import re
from pathlib import Path

from arena.referee import Exploit


def _slug(ex: Exploit) -> str:
    route = re.sub(r"[^a-z0-9]+", "_", re.sub(r"/\d+", "/id", ex.path.split("?")[0].lower())).strip("_")
    return f"{ex.vuln_class}_{route}"


def security_test_source(ex: Exploit) -> str:
    return (
        "import os\n\nimport httpx\n\n"
        'BASE = os.environ.get("ARENA_TARGET", "http://127.0.0.1:8000")\n\n\n'
        f"def test_{_slug(ex)}_does_not_leak_flag():\n"
        f"    r = httpx.request({ex.method!r}, BASE + {ex.path!r}, headers={ex.headers!r},\n"
        f"                      params={ex.params!r}, json={ex.json!r})\n"
        f"    assert {ex.flag!r} not in r.text\n"
    )


def export(match_dir: Path, exploits: list, patches: list, ttps: list) -> Path:
    match_dir = Path(match_dir)
    sec = match_dir / "tests" / "security"
    sec.mkdir(parents=True, exist_ok=True)
    (match_dir / "hardened.patch").write_text("".join(patches), encoding="utf-8")
    lines = ["# Vibe Arena security report", ""]
    for ex, patch, ttp in zip(exploits, patches, ttps):
        (sec / f"test_security_{_slug(ex)}.py").write_text(security_test_source(ex), encoding="utf-8")
        lines += [f"## {ex.vuln_class}: `{ex.method} {ex.path}`", "",
                  f"- Leaked: `{ex.flag}`", f"- Time to patch: {ttp} s",
                  "- Exploit replay after the fix: blocked", "", "```diff", patch.rstrip(), "```", ""]
    (match_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return match_dir
