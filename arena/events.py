"""Event log: every event is numbered, written to a JSONL file, kept in memory, and fanned out."""
import asyncio
import json
import time
from pathlib import Path


class EventLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")
        self.events: list[dict] = []
        self._subs: list[tuple[asyncio.Queue, asyncio.AbstractEventLoop]] = []
        self._t0 = time.time()
        self.echo = False

    def emit(self, event: dict) -> None:
        event = dict(event, seq=len(self.events), ts=round(time.time() - self._t0, 2))
        self.events.append(event)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        if self.echo:
            rest = {k: v for k, v in event.items() if k not in ('seq', 'ts', 'type', 'patch')}
            print(f"[{event['seq']:>3}] {event['type']:<14} {str(rest)[:110]}")
        for q, loop in self._subs:
            loop.call_soon_threadsafe(q.put_nowait, event)

    def subscribe(self, loop: asyncio.AbstractEventLoop) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subs.append((q, loop))
        return q
