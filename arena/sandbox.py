"""Runs target-app copies as subprocesses, each with its own DB copy and port."""
import itertools
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx
import psutil

ALLOWED_PORTS: set[int] = set()


class TargetBootError(RuntimeError):
    pass


class PortAllocator:
    def __init__(self, start: int = 8001):
        self._counter = itertools.count(start)

    def next(self) -> int:
        return next(self._counter)


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
                 app_module: str = "app.main:app"):
        self.src_dir, self.seed_db, self.port = Path(src_dir), Path(seed_db), port
        self.work_root, self.app_module = Path(work_root), app_module
        self._proc: subprocess.Popen | None = None

    @property
    def dir(self) -> Path:
        return self.work_root / str(self.port)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def prepare(self) -> Path:
        if self.dir.exists():
            shutil.rmtree(self.dir)
        self.dir.mkdir(parents=True)
        shutil.copytree(self.src_dir / "app", self.dir / "app",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(self.seed_db, self.dir / "seed.db")
        return self.dir

    def start(self, timeout: float = 15) -> None:
        env = dict(os.environ, ARENA_DB=str(self.dir / "seed.db"))
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", self.app_module, "--port", str(self.port),
             "--log-level", "warning"],
            cwd=self.dir, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
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
        raise TargetBootError(f"target on port {self.port} failed to boot")

    def stop(self) -> None:
        if self._proc is not None:
            kill_tree(self._proc.pid)
            self._proc = None
        ALLOWED_PORTS.discard(self.port)
