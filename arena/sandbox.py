"""Runs target-app copies as subprocesses, each with its own DB copy and port."""
import itertools
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import psutil

ALLOWED_PORTS: set[int] = set()
# Demo mode: targets deliberately left running after a match so the victim site stays
# browsable. They are killed before the next match starts, never leaked across runs.
KEPT: list["TargetProcess"] = []


class TargetBootError(RuntimeError):
    pass


def stop_kept() -> None:
    while KEPT:
        KEPT.pop().stop()


def port_is_free(port: int) -> bool:
    """True when nothing is listening on 127.0.0.1:port.

    A demo target kept alive for filming holds its port in another process, so a new match must not
    be handed that port: uvicorn would fail to bind and the match would abort on boot.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


class PortAllocator:
    def __init__(self, start: int = 8001):
        self._counter = itertools.count(start)

    def next(self) -> int:
        for _ in range(200):
            port = next(self._counter)
            if port in ALLOWED_PORTS or not port_is_free(port):
                continue
            return port
        raise RuntimeError(f"no free port above {start}")


def kill_tree(pid: int) -> None:
    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return
    for child in proc.children(recursive=True):
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass
    try:
        proc.kill()
        proc.wait(timeout=5)
    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
        pass


class TargetProcess:
    def __init__(self, src_dir: Path, seed_db: Path, port: int, work_root: Path,
                 app_module: str = "app.main:app", extra_paths: list | None = None):
        self.src_dir, self.seed_db, self.port = Path(src_dir), Path(seed_db), port
        self.work_root, self.app_module = Path(work_root).resolve(), app_module
        self.extra_paths = list(extra_paths or [])
        self._proc: subprocess.Popen | None = None
        self._log: object | None = None

    @property
    def dir(self) -> Path:
        return self.work_root / str(self.port)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def prepare(self) -> Path:
        if self.dir.exists():
            shutil.rmtree(self.dir)
        self.dir.mkdir(parents=True)
        shutil.copytree(self.src_dir / "app", self.dir / "app",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(self.seed_db, self.dir / "seed.db")
        for rel in self.extra_paths:
            src = self.src_dir / rel
            if src.is_dir():
                shutil.copytree(src, self.dir / rel, ignore=shutil.ignore_patterns("__pycache__"))
            elif src.is_file():
                shutil.copy(src, self.dir / rel)
        return self.dir

    def start(self, timeout: float = 15) -> None:
        env = dict(os.environ, ARENA_DB=str(self.dir / "seed.db"))
        self._log = open(self.dir / "boot.log", "wb")
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", self.app_module, "--port", str(self.port),
             "--log-level", "warning"],
            cwd=self.dir, env=env, stdout=self._log, stderr=self._log,
        )
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._proc.poll() is not None:
                break
            try:
                if httpx.get(self.url + "/openapi.json", timeout=1).status_code == 200:
                    ALLOWED_PORTS.add(self.port)
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.25)
        self.stop()
        tail = ""
        try:
            tail = (self.dir / "boot.log").read_text(errors="replace")[-800:].strip()
        except OSError:
            pass
        raise TargetBootError(f"target on port {self.port} failed to boot: {tail}")

    def stop(self) -> None:
        if self._proc is not None:
            kill_tree(self._proc.pid)
            self._proc = None
        if self._log is not None:
            try:
                self._log.close()
            finally:
                self._log = None
        ALLOWED_PORTS.discard(self.port)
