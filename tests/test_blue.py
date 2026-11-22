from pathlib import Path

import pytest

from arena.blue import (EditApplyError, apply_edits, make_patch, parse_edits, run_blue)
from arena.config import load_config
from arena.referee import Exploit, verify_patch
from arena.sandbox import ALLOWED_PORTS, PortAllocator, TargetProcess
from tests.fakes import FakeLLM

ROOT = Path(__file__).resolve().parent.parent
CFG = load_config(str(ROOT / "arena.yaml"))

SEARCH = '''    current_user(authorization)
    conn = get_conn()
    row = conn.execute(
        "SELECT id, owner_id, amount, note FROM invoices WHERE id = ?", (invoice_id,)'''
FIX = '''    user = current_user(authorization)
    conn = get_conn()
    row = conn.execute(
        "SELECT id, owner_id, amount, note FROM invoices WHERE id = ? AND owner_id = ?",
        (invoice_id, user["id"])'''
DENY_ALL = '''    raise HTTPException(403, "denied")
    conn = get_conn()
    row = conn.execute(
        "SELECT id, owner_id, amount, note FROM invoices WHERE id = ?", (invoice_id,)'''


def block(search, replace, path="app/routes/invoices.py"):
    return f"FILE: {path}\n<<<<<<< SEARCH\n{search}\n=======\n{replace}\n>>>>>>> REPLACE\n"


IDOR = Exploit("GET", "/api/invoices/3", {"Authorization": "Bearer tok-1"}, None, None,
               "FLAG{idor_invoice_leak}", "idor")


def staging_with(tmp_path, port, replace):
    t = TargetProcess(CFG.app_dir, CFG.seed_db, port, tmp_path, extra_paths=CFG.extra_paths)
    t.prepare()
    apply_edits(t.dir, parse_edits(block(SEARCH, replace)))
    t.start()
    return t


def test_parse_and_apply_edit(tmp_path):
    (tmp_path / "app").mkdir()
    f = tmp_path / "app" / "x.py"
    f.write_text("a = 1\nb = 2\n")
    edits = parse_edits("```\nFILE: app/x.py\n<<<<<<< SEARCH\na = 1\n=======\na = 9\n>>>>>>> REPLACE\n```")
    assert len(edits) == 1
    apply_edits(tmp_path, edits)
    assert f.read_text() == "a = 9\nb = 2\n"


def test_apply_crlf_tolerant(tmp_path):
    (tmp_path / "app").mkdir()
    f = tmp_path / "app" / "x.py"
    f.write_bytes(b"def f():\r\n    return 1\r\n")
    apply_edits(tmp_path, parse_edits(
        "FILE: app/x.py\n<<<<<<< SEARCH\ndef f():\n    return 1\n=======\ndef f():\n    return 2\n>>>>>>> REPLACE\n"))
    assert "return 2" in f.read_text()


def test_apply_missing_search_raises(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "x.py").write_text("a = 1\n")
    with pytest.raises(EditApplyError):
        apply_edits(tmp_path, parse_edits(block("not there", "x", "app/x.py")))


def test_apply_rejects_path_escape(tmp_path):
    (tmp_path / "app").mkdir()
    with pytest.raises(EditApplyError):
        apply_edits(tmp_path, parse_edits(block("a", "b", "../evil.py")))


def test_make_patch_has_headers(tmp_path):
    for d, v in (("before", "x = 1\n"), ("after", "x = 2\n")):
        (tmp_path / d / "app").mkdir(parents=True)
        (tmp_path / d / "app" / "m.py").write_text(v)
    patch = make_patch(tmp_path / "before", tmp_path / "after")
    assert "--- a/app/m.py" in patch and "+++ b/app/m.py" in patch and "-x = 1" in patch


def test_verify_accepts_real_fix(tmp_path):
    t = staging_with(tmp_path, 9700, FIX)
    try:
        v = verify_patch(t, IDOR, CFG.functional_tests)
        assert v.ok and not v.replay_flag_found and v.tests.failed == 0
    finally:
        t.stop()


def test_verify_rejects_403_everyone(tmp_path):
    t = staging_with(tmp_path, 9710, DENY_ALL)
    try:
        v = verify_patch(t, IDOR, CFG.functional_tests)
        assert not v.ok and v.tests.failed >= 1
    finally:
        t.stop()


def test_blue_end_to_end_accepts_fix(tmp_path):
    live = TargetProcess(CFG.app_dir, CFG.seed_db, 9720, tmp_path, extra_paths=CFG.extra_paths)
    live.prepare(); live.start()
    events = []
    try:
        llm = FakeLLM([{"content": block(SEARCH, FIX), "tool_calls": []}])
        res = run_blue(llm, live.dir, CFG.seed_db, IDOR, "", CFG.functional_tests,
                       PortAllocator(9721), tmp_path, events.append, extra_paths=CFG.extra_paths)
        assert res.ok and res.attempts == 1 and res.new_target.port != live.port
        assert "owner_id" in res.patch and "--- a/app/routes/invoices.py" in res.patch
        res.new_target.stop()
    finally:
        live.stop()
    assert any(e["type"] == "blue_attempt" and e["ok"] for e in events)


def test_blue_retries_then_gives_up(tmp_path):
    live = TargetProcess(CFG.app_dir, CFG.seed_db, 9730, tmp_path, extra_paths=CFG.extra_paths)
    live.prepare(); live.start()
    try:
        bad = {"content": block("this text is not in the file", "x"), "tool_calls": []}
        llm = FakeLLM([bad, bad, bad])
        res = run_blue(llm, live.dir, CFG.seed_db, IDOR, "", CFG.functional_tests,
                       PortAllocator(9731), tmp_path, lambda e: None, extra_paths=CFG.extra_paths)
        assert not res.ok and res.attempts == 3 and llm.calls == 3
        assert ALLOWED_PORTS == {live.port}
    finally:
        live.stop()


TRAV_OLD = '''    path = Path("files") / name
    if not path.is_file():'''
TRAV_FIX = '''    base = Path("files").resolve()
    path = (base / name).resolve()
    if base not in path.parents or not path.is_file():'''
TRAVERSAL = Exploit("GET", "/api/files", None, {"name": "../secret.txt"}, None,
                    "FLAG{path_traversal_leak}", "path_traversal")


def test_verify_accepts_real_traversal_fix(tmp_path):
    t = TargetProcess(CFG.app_dir, CFG.seed_db, 9740, tmp_path, extra_paths=CFG.extra_paths)
    t.prepare()
    apply_edits(t.dir, parse_edits(block(TRAV_OLD, TRAV_FIX, "app/routes/files.py")))
    t.start()
    try:
        v = verify_patch(t, TRAVERSAL, CFG.functional_tests)
        assert v.ok and not v.replay_flag_found
    finally:
        t.stop()
