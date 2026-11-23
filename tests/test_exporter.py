from pathlib import Path

from arena.blue import apply_edits, parse_edits
from arena.config import load_config
from arena.exporter import export, security_test_source
from arena.referee import Exploit, run_functional_tests
from arena.sandbox import TargetProcess
from tests.test_blue import FIX, IDOR, SEARCH, block

ROOT = Path(__file__).resolve().parent.parent
CFG = load_config(str(ROOT / "arena.yaml"))

IDOR_LOGIN = Exploit("GET", "/api/invoices/3", {"Authorization": "Bearer tok-stale"}, None, None,
                     "FLAG{idor_invoice_leak}", "idor",
                     login={"path": "/api/login",
                            "json": {"username": "alice", "password": "alice123"}})


def run_security_suite(tmp_path, port, fixed, exploit=IDOR):
    out = tmp_path / f"sec{port}"
    out.mkdir()
    (out / "test_security_idor.py").write_text(security_test_source(exploit))
    t = TargetProcess(CFG.app_dir, CFG.seed_db, port, tmp_path)
    t.prepare()
    if fixed:
        apply_edits(t.dir, parse_edits(block(SEARCH, FIX)))
    t.start()
    try:
        return run_functional_tests(out, t.url)
    finally:
        t.stop()


def test_security_test_fails_when_vulnerable_passes_when_fixed(tmp_path):
    assert run_security_suite(tmp_path, 9810, fixed=False).failed == 1
    r = run_security_suite(tmp_path, 9811, fixed=True)
    assert r.failed == 0 and r.passed == 1


def test_exported_test_logs_in_again_instead_of_reusing_a_stale_token(tmp_path):
    assert run_security_suite(tmp_path, 9820, fixed=False, exploit=IDOR_LOGIN).failed == 1
    r = run_security_suite(tmp_path, 9821, fixed=True, exploit=IDOR_LOGIN)
    assert r.failed == 0 and r.passed == 1


def test_export_writes_files(tmp_path):
    export(tmp_path, [IDOR], ["--- a/app/x.py\n+++ b/app/x.py\n"], [8.4])
    assert (tmp_path / "hardened.patch").read_text().startswith("--- a/app/x.py")
    assert list((tmp_path / "tests" / "security").glob("test_security_*.py"))
    report = (tmp_path / "report.md").read_text()
    assert "FLAG{idor_invoice_leak}" in report and "8.4" in report
