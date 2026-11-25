"""python -m arena.cli run|replay|serve"""
import argparse
import json
import os
import time
from pathlib import Path


def _line(e):
    rest = {k: v for k, v in e.items() if k not in ("seq", "ts", "type", "patch")}
    return f"[{e['seq']:>3}] {e['type']:<14} {str(rest)[:110]}"


def cmd_run(a):
    import httpx

    from arena.capture import capture_tests, review_tests
    from arena.config import load_config
    from arena.events import EventLog
    from arena.llm import LLM
    from arena.orchestrator import run_match
    from arena.sandbox import PortAllocator, TargetProcess

    cfg = load_config(a.config)
    if a.strategy:
        cfg.strategy = a.strategy
    red, blue = LLM("red"), LLM("blue")
    match_id = "live-" + time.strftime("%Y%m%d-%H%M%S")
    work = Path("work") / match_id
    if a.capture:
        t = TargetProcess(cfg.app_dir, cfg.seed_db, PortAllocator(7900).next(), work / "capture",
                          cfg.app_module, cfg.extra_paths)
        t.prepare()
        t.start()
        try:
            frozen = work / "frozen_tests"
            spec = httpx.get(t.url + "/openapi.json").json()
            res = capture_tests(blue, spec, cfg, t.url, frozen)
            print(f"captured {len(res.kept)} tests, dropped {len(res.dropped)}")
            if not a.yes:
                review_tests(frozen)
            if res.kept:
                cfg.functional_tests = frozen
        finally:
            t.stop()
    log = EventLog(Path("matches") / match_id / "events.jsonl")
    log.echo = True
    keep = a.keep_target or os.environ.get("ARENA_KEEP_TARGET", "0") == "1"
    s = run_match(cfg, red, blue, log, rounds=a.rounds, work_root=work,
                  out_dir=Path("matches") / match_id, explore=a.explore, keep_target=keep)
    print(f"\nRed {s.red} - Blue {s.blue} | closed {s.closed}/{s.total} | tokens {s.tokens} | "
          f"ttp {s.ttp}\nsweep {s.sweep_findings} findings in {s.sweep_requests} requests | "
          f"llm calls {s.llm_calls} | cache hits {s.cache_hits}\nExports in matches/{match_id}/")
    if keep:
        print(f"Target kept alive at http://127.0.0.1:{s.final_port} — open http://127.0.0.1:8765/target "
              f"to watch it, and stop that python process when you are done.")


def cmd_replay(a):
    for line in Path(a.file).read_text(encoding="utf-8").splitlines():
        if line.strip():
            print(_line(json.loads(line)))


def cmd_serve(a):
    import uvicorn

    uvicorn.run("arena.server:app", host="127.0.0.1", port=a.port)


def main():
    p = argparse.ArgumentParser(prog="arena")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--config", default=os.environ.get("ARENA_CONFIG", "arena.yaml"))
    r.add_argument("--yes", action="store_true")
    r.add_argument("--capture", action="store_true")
    r.add_argument("--rounds", type=int, default=3)
    r.add_argument("--strategy", choices=("hybrid", "sweep", "llm"), default=None)
    r.add_argument("--explore", action="store_true",
                   help="also run the LLM Red pass when the sweep already found bugs")
    r.add_argument("--keep-target", action="store_true",
                   help="leave the patched target running after the verdict so /target stays browsable")
    r.set_defaults(fn=cmd_run)
    rp = sub.add_parser("replay")
    rp.add_argument("file")
    rp.set_defaults(fn=cmd_replay)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8765)
    s.set_defaults(fn=cmd_serve)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
