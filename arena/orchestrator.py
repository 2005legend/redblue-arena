"""Runs a match: Red attacks, Blue patches, the referee verifies, and everything is logged."""
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from arena.blue import run_blue
from arena.events import EventLog
from arena.exporter import export
from arena.red import normalize_route, run_red
from arena.referee import find_flags, replay, run_functional_tests
from arena.sandbox import PortAllocator, TargetProcess


@dataclass
class MatchSummary:
    red: int = 0
    blue: int = 0
    closed: int = 0
    total: int = 0
    tokens: int = 0
    ttp: list = field(default_factory=list)
    first_port: int = 0
    final_port: int = 0


def run_match(cfg, llm_red, llm_blue, log: EventLog, rounds: int = 3, work_root: Path = Path("work"),
              out_dir: Path = Path("matches/last"), base_port: int = 8001) -> MatchSummary:
    emit = log.emit
    ports = PortAllocator(base_port)
    work_root, out_dir = Path(work_root), Path(out_dir)
    live = TargetProcess(cfg.app_dir, cfg.seed_db, ports.next(), work_root, cfg.app_module)
    live.prepare()
    live.start()
    summary = MatchSummary(first_port=live.port)
    exploits_closed, patches, ttps = [], [], []
    seen_routes: set[str] = set()
    try:
        openapi = httpx.get(live.url + "/openapi.json").json()
        emit({"type": "match_start", "routes": sorted(
            {p for p in openapi.get("paths", {}) if not p.startswith("/openapi")})})
        h = run_functional_tests(cfg.functional_tests, live.url)
        emit({"type": "health", "passed": h.passed, "failed": h.failed})
        for _ in range(rounds):
            found = run_red(llm_red, live.url, openapi, cfg.users, emit)
            if not found:
                break
            for ex in found:
                route = normalize_route(ex.path)
                if (ex.vuln_class, route) in seen_routes:
                    continue
                if ex.flag not in find_flags(replay(ex, live.url).body):
                    continue  # an earlier patch in this round already closed it
                seen_routes.add((ex.vuln_class, route))
                summary.red += 1
                summary.total += 1
                emit({"type": "score", "red": summary.red, "blue": summary.blue})
                start = time.time()
                res = run_blue(llm_blue, live.dir, cfg.seed_db, ex, "", cfg.functional_tests,
                               ports, work_root, emit, app_module=cfg.app_module)
                if not res.ok:
                    continue
                old, live = live, res.new_target
                old.stop()
                ttp = round(time.time() - start, 1)
                summary.blue += 1
                summary.closed += 1
                summary.ttp.append(ttp)
                exploits_closed.append(ex)
                patches.append(res.patch)
                ttps.append(ttp)
                emit({"type": "patched", "route": route, "vuln_class": ex.vuln_class,
                      "patch": res.patch, "ttp_seconds": ttp})
                emit({"type": "score", "red": summary.red, "blue": summary.blue})
                h = run_functional_tests(cfg.functional_tests, live.url)
                emit({"type": "health", "passed": h.passed, "failed": h.failed})
        summary.final_port = live.port
        summary.tokens = getattr(llm_red, "tokens_used", 0) + getattr(llm_blue, "tokens_used", 0)
        export(out_dir, exploits_closed, patches, ttps)
        emit({"type": "match_end", "summary": summary.__dict__,
              "files": ["hardened.patch", "report.md"]})
    finally:
        live.stop()
    return summary
