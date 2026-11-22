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
