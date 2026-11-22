from pathlib import Path

from arena.capture import capture_tests, verify_frozen
from arena.config import load_config
from arena.sandbox import TargetProcess
from tests.fakes import FakeLLM

ROOT = Path(__file__).resolve().parent.parent
CFG = load_config(str(ROOT / "arena.yaml"))

HEAD = '''import os, httpx
BASE = os.environ["ARENA_TARGET"]
def tok():
    return httpx.post(BASE + "/api/login", json={"username": "alice", "password": "alice123"}).json()["token"]
'''
OWN = HEAD + '''def test_own():
    assert httpx.get(BASE + "/api/invoices/1", headers={"Authorization": "Bearer " + tok()}).status_code == 200
'''
CROSS = HEAD + '''def test_cross():
    assert httpx.get(BASE + "/api/invoices/3", headers={"Authorization": "Bearer " + tok()}).status_code == 200
'''
BROKEN = HEAD + '''def test_broken():
    assert httpx.get(BASE + "/api/invoices/1", headers={"Authorization": "Bearer " + tok()}).status_code == 418
'''


def reply(**files):
    text = "\n".join(f"### {n}.py\n```python\n{src}```" for n, src in files.items())
    return {"content": text, "tool_calls": []}


def test_capture_filters_cross_user_and_failing(tmp_path):
    t = TargetProcess(CFG.app_dir, CFG.seed_db, 9800, tmp_path)
    t.prepare(); t.start()
    try:
        llm = FakeLLM([reply(test_own=OWN, test_cross=CROSS, test_broken=BROKEN)])
        res = capture_tests(llm, {"paths": {}}, CFG, t.url, tmp_path / "frozen")
    finally:
        t.stop()
    assert res.kept == ["test_own.py"]
    assert sorted(res.dropped) == ["test_broken.py", "test_cross.py"]
    assert verify_frozen(tmp_path / "frozen")
    (tmp_path / "frozen" / "test_own.py").write_text("# tampered\n")
    assert not verify_frozen(tmp_path / "frozen")
