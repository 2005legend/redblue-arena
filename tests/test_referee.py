from pathlib import Path

from arena.config import load_config
from arena.referee import Exploit, find_flags, replay
from arena.sandbox import PortAllocator, TargetProcess

ROOT = Path(__file__).resolve().parent.parent
CFG = load_config(str(ROOT / "arena.yaml"))


def test_find_flags():
    assert find_flags("a FLAG{one_1} b FLAG{two}") == ["FLAG{one_1}", "FLAG{two}"]
    assert find_flags("nothing here") == []


def test_replay_returns_flag_on_dev_target(tmp_path):
    t = TargetProcess(CFG.app_dir, CFG.seed_db, PortAllocator(9500).next(), tmp_path)
    t.prepare(); t.start()
    try:
        ex = Exploit(method="GET", path="/api/invoices/3",
                     headers={"Authorization": "Bearer tok-1"}, params=None, json=None,
                     flag="FLAG{idor_invoice_leak}", vuln_class="idor")
        assert ex.flag in find_flags(replay(ex, t.url).body)
    finally:
        t.stop()


def test_replay_path_traversal_leaks_flag(tmp_path):
    t = TargetProcess(CFG.app_dir, CFG.seed_db, PortAllocator(9510).next(), tmp_path,
                      extra_paths=CFG.extra_paths)
    t.prepare(); t.start()
    try:
        ex = Exploit(method="GET", path="/api/files", headers=None, params={"name": "../secret.txt"},
                     json=None, flag="FLAG{path_traversal_leak}", vuln_class="path_traversal")
        assert ex.flag in find_flags(replay(ex, t.url).body)
    finally:
        t.stop()


def test_replay_relogs_in_so_a_stale_token_cannot_hide_a_bug(tmp_path):
    t = TargetProcess(CFG.app_dir, CFG.seed_db, PortAllocator(9520).next(), tmp_path,
                      extra_paths=CFG.extra_paths)
    t.prepare(); t.start()
    try:
        ex = Exploit(method="GET", path="/api/invoices/3",
                     headers={"Authorization": "Bearer tok-stale"}, params=None, json=None,
                     flag="FLAG{idor_invoice_leak}", vuln_class="idor",
                     login={"path": "/api/login", "json": {"username": "alice", "password": "alice123"}})
        assert ex.flag in find_flags(replay(ex, t.url).body)
        no_login = Exploit("GET", "/api/invoices/3", {"Authorization": "Bearer tok-stale"}, None, None,
                           "FLAG{idor_invoice_leak}", "idor")
        assert ex.flag not in find_flags(replay(no_login, t.url).body)
    finally:
        t.stop()


def test_find_token_reads_common_shapes():
    from arena.referee import find_token
    assert find_token('{"token": "tok-7"}') == "tok-7"
    assert find_token('{"access_token": "abc"}') == "abc"
    assert find_token("not json") is None
