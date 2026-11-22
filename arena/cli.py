"""python -m arena.cli run|replay|serve"""
import argparse
import json
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
    red, blue = LLM("red"), LLM("blue")
    match_id = "live-" + time.strftime("%Y%m%d-%H%M%S")
    work = Path("work") / match_id
    if a.capture:
        t = TargetProcess(cfg.app_dir, cfg.seed_db, PortAllocator(7900).next(), work / "capture",
                          cfg.app_module)
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
    s = run_match(cfg, red, blue, log, rounds=a.rounds, work_root=work,
                  out_dir=Path("matches") / match_id)
    print(f"\nRed {s.red} - Blue {s.blue} | closed {s.closed}/{s.total} | tokens {s.tokens} | "
          f"ttp {s.ttp}\nExports in matches/{match_id}/")


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
    r.add_argument("--config", default="arena.yaml")
    r.add_argument("--yes", action="store_true")
    r.add_argument("--capture", action="store_true")
    r.add_argument("--rounds", type=int, default=3)
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
