"""Runs a match: Red attacks, Blue patches, the referee verifies, and everything is logged."""
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from arena.blue import run_blue
from arena.config import attacker_accounts
from arena.events import EventLog
from arena.exporter import export
from arena.llm import BudgetExceeded
from arena.red import normalize_route, run_red
from arena.referee import find_flags, replay, run_functional_tests
from arena.sandbox import KEPT, PortAllocator, TargetProcess, stop_kept
from arena.sweep import Sweep, should_run_llm


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
    sweep_findings: int = 0
    sweep_requests: int = 0
    llm_calls: int = 0
    cache_hits: int = 0
    red_tokens: int = 0
    blue_tokens: int = 0
    red_llm_calls: int = 0
    blue_llm_calls: int = 0


def run_match(cfg, llm_red, llm_blue, log: EventLog, rounds: int = 3, work_root: Path = Path("work"),
              out_dir: Path = Path("matches/last"), base_port: int = 8001,
              strategy: str | None = None, explore: bool = False,
              cache_path: Path | None = None, keep_target: bool = False) -> MatchSummary:
    emit = log.emit
    strategy = strategy or cfg.strategy
    cache_path = cfg.cache_path if cache_path is None else cache_path
    # A target kept alive from an earlier demo match would hold its port (and the
    # allow-list entry), so clear those before allocating new ones.
    stop_kept()
    ports = PortAllocator(base_port)
    work_root, out_dir = Path(work_root), Path(out_dir)
    live = TargetProcess(cfg.app_dir, cfg.seed_db, ports.next(), work_root, cfg.app_module,
                       cfg.extra_paths)
    live.prepare()
    live.start()
    emit({"type": "target_live", "url": live.url, "port": live.port})
    summary = MatchSummary(first_port=live.port)
    exploits_closed, patches, ttps = [], [], []
    seen_routes: set[tuple[str, str]] = set()
    seen_flags: set[str] = set()
    try:
        openapi = httpx.get(live.url + "/openapi.json").json()
        emit({"type": "match_start", "strategy": strategy, "routes": sorted(
            {p for p in openapi.get("paths", {}) if not p.startswith("/openapi")})})
        h = run_functional_tests(cfg.functional_tests, live.url)
        emit({"type": "health", "passed": h.passed, "failed": h.failed})
        sweep_findings = []
        if strategy in ("hybrid", "sweep"):
            sweeper = Sweep(live.url, openapi, attacker_accounts(cfg),
                            flag_owners=cfg.flag_owners, admin_routes=cfg.admin_routes,
                            login_path=cfg.login_path, loot_paths=cfg.loot_paths, emit=emit)
            emit({"type": "sweep_start"})
            sweep_findings = sweeper.run()
            summary.sweep_findings = len(sweep_findings)
            summary.sweep_requests = sweeper.requests
            emit({"type": "sweep_done", "findings": len(sweep_findings),
                  "requests": sweeper.requests})
        try:
            allow_llm = should_run_llm(strategy, sweep_findings, explore)
            for rnd in range(rounds):
                found = list(sweep_findings) if rnd == 0 else []
                if allow_llm:
                    found.extend(run_red(llm_red, live.url, openapi, attacker_accounts(cfg), emit,
                                         flag_owners=cfg.flag_owners, login_path=cfg.login_path))
                if not found:
                    break
                for ex in found:
                    route = normalize_route(ex.path)
                    if ex.flag in seen_flags or (ex.vuln_class, route) in seen_routes:
                        continue
                    if ex.flag not in find_flags(replay(ex, live.url).body):
                        continue  # an earlier patch in this round already closed it
                    seen_flags.add(ex.flag)
                    seen_routes.add((ex.vuln_class, route))
                    summary.red += 1
                    summary.total += 1
                    emit({"type": "score", "red": summary.red, "blue": summary.blue})
                    start = time.time()
                    try:
                        res = run_blue(llm_blue, live.dir, cfg.seed_db, ex, "",
                                       cfg.functional_tests, ports, work_root, emit,
                                       app_module=cfg.app_module, extra_paths=cfg.extra_paths,
                                       cache_path=cache_path)
                    except BudgetExceeded:
                        raise
                    except RuntimeError as exc:  # provider down: keep going, still export
                        emit({"type": "blue_error", "error": str(exc)})
                        continue
                    if not res.ok:
                        continue
                    if res.cached:
                        summary.cache_hits += 1
                    old, live = live, res.new_target
                    old.stop()
                    emit({"type": "target_live", "url": live.url, "port": live.port})
                    ttp = round(time.time() - start, 1)
                    summary.blue += 1
                    summary.closed += 1
                    summary.ttp.append(ttp)
                    exploits_closed.append(ex)
                    patches.append(res.patch)
                    ttps.append(ttp)
                    emit({"type": "patched", "route": route, "vuln_class": ex.vuln_class,
                          "cached": res.cached, "patch": res.patch, "ttp_seconds": ttp})
                    emit({"type": "score", "red": summary.red, "blue": summary.blue})
                    h = run_functional_tests(cfg.functional_tests, live.url)
                    emit({"type": "health", "passed": h.passed, "failed": h.failed})
        except BudgetExceeded as exc:  # still export what was closed before the budget ran out
            emit({"type": "budget_exceeded", "error": str(exc)})
        summary.final_port = live.port
        summary.red_tokens = getattr(llm_red, "tokens_used", 0)
        summary.blue_tokens = getattr(llm_blue, "tokens_used", 0)
        summary.red_llm_calls = getattr(llm_red, "calls", 0)
        summary.blue_llm_calls = getattr(llm_blue, "calls", 0)
        summary.tokens = summary.red_tokens + summary.blue_tokens
        summary.llm_calls = summary.red_llm_calls + summary.blue_llm_calls
        export(out_dir, exploits_closed, patches, ttps)
        # Emit this before match_end: consumers (and tests) treat match_end as the
        # terminal event. In demo mode the target is kept alive instead.
        if not keep_target:
            emit({"type": "target_down", "port": live.port})
        emit({"type": "match_end", "summary": summary.__dict__,
              "files": ["hardened.patch", "report.md"]})
    finally:
        if keep_target and live.running:
            KEPT.append(live)  # demo mode: leave the victim site browsable after the verdict
        else:
            live.stop()
    return summary
