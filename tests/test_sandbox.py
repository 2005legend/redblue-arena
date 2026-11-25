import socket
import sqlite3
from pathlib import Path

import httpx
import pytest

from arena.config import load_config
from arena.sandbox import ALLOWED_PORTS, PortAllocator, TargetBootError, TargetProcess, port_is_free

ROOT = Path(__file__).resolve().parent.parent
CFG = load_config(str(ROOT / "arena.yaml"))


def make(port, tmp_path, src=None):
    return TargetProcess(src or CFG.app_dir, CFG.seed_db, port, tmp_path)


def port_open(port):
    s = socket.socket()
    s.settimeout(0.5)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def test_ports_never_repeat():
    p = PortAllocator(start=9100)
    got = [p.next() for _ in range(5)]
    assert got == sorted(set(got)) and got[0] == 9100


def test_allocator_skips_a_port_something_else_holds():
    """A kept demo target (or any other process) holds its port; a new match must not be handed it."""
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.bind(("127.0.0.1", 0))
    holder.listen(1)
    busy = holder.getsockname()[1]
    try:
        assert not port_is_free(busy)
        picked = PortAllocator(busy).next()
    finally:
        holder.close()
    assert picked > busy and port_is_free(picked)


def test_start_and_stop(tmp_path):
    t = make(PortAllocator(9200).next(), tmp_path)
    t.prepare()
    t.start()
    try:
        assert httpx.get(t.url + "/openapi.json").status_code == 200
        assert t.port in ALLOWED_PORTS
    finally:
        t.stop()
    assert not port_open(t.port) and t.port not in ALLOWED_PORTS


def test_two_targets_isolated_db(tmp_path):
    a, b = make(9300, tmp_path), make(9301, tmp_path)
    a.prepare(); b.prepare()
    c = sqlite3.connect(a.dir / "seed.db")
    c.execute("UPDATE invoices SET amount = 1234 WHERE id = 1")
    c.commit(); c.close()
    cb = sqlite3.connect(b.dir / "seed.db")
    amount = cb.execute("SELECT amount FROM invoices WHERE id = 1").fetchone()[0]
    cb.close()
    assert amount == 19.5


def test_boot_failure_raises(tmp_path):
    bad = tmp_path / "bad_src"
    (bad / "app").mkdir(parents=True)
    (bad / "app" / "main.py").write_text("def broken(:\n")
    (bad / "app" / "__init__.py").write_text("")
    t = make(9400, tmp_path, src=bad)
    t.prepare()
    with pytest.raises(TargetBootError):
        t.start(timeout=5)
    assert not port_open(9400) and 9400 not in ALLOWED_PORTS


def test_extra_paths_copied(tmp_path):
    t = TargetProcess(CFG.app_dir, CFG.seed_db, 9450, tmp_path, extra_paths=CFG.extra_paths)
    t.prepare()
    assert (t.dir / "files" / "welcome.txt").is_file()
    assert (t.dir / "secret.txt").is_file()


def test_relative_work_root_still_finds_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    t = TargetProcess(CFG.app_dir, CFG.seed_db, 9460, Path("work_rel"), extra_paths=CFG.extra_paths)
    t.prepare()
    t.start()
    try:
        r = httpx.post(t.url + "/api/login", json={"username": "alice", "password": "alice123"})
        assert r.status_code == 200
    finally:
        t.stop()
