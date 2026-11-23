"""Blue agent: asks the LLM for SEARCH/REPLACE edits, verifies them on a staging copy."""
import difflib
import re
from dataclasses import dataclass
from pathlib import Path

from arena.referee import Exploit, verify_patch
from arena.sandbox import PortAllocator, TargetBootError, TargetProcess

SYSTEM = (
    "You are the Blue agent defending a small FastAPI app. A red attacker just exploited it. "
    "Fix the ROOT CAUSE in the source with the smallest change that keeps normal behaviour "
    "working (normal users must still log in, search, and read their own data; admins must "
    "still use admin routes). Do not delete routes and do not reject everyone. Reply ONLY with "
    "one or more edit blocks in exactly this format, copying SEARCH text exactly from the files:\n\n"
    "FILE: app/routes/example.py\n<<<<<<< SEARCH\n(existing lines)\n=======\n(replacement lines)\n"
    ">>>>>>> REPLACE"
)

EDIT_RE = re.compile(
    r"FILE:\s*[`*]*([^\s`*]+)[`*]*\s*\n<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)>>>>>>> REPLACE", re.S)


class EditApplyError(Exception):
    pass


@dataclass
class Edit:
    path: str
    search: str
    replace: str


@dataclass
class BlueResult:
    ok: bool
    patch: str
    new_target: TargetProcess | None
    attempts: int


def parse_edits(text: str) -> list[Edit]:
    edits = []
    for path, search, replace in EDIT_RE.findall(text or ""):
        edits.append(Edit(path, search.replace("\r\n", "\n"),
                          replace[:-1] if replace.endswith("\n") else replace))
    return edits


def apply_edits(app_root: Path, edits: list[Edit]) -> None:
    app_root = Path(app_root).resolve()
    for e in edits:
        target = (app_root / e.path).resolve()
        if not target.is_relative_to((app_root / "app").resolve()) or target.suffix != ".py":
            raise EditApplyError(f"{e.path}: edits are only allowed on app/**/*.py")
        if not target.is_file():
            raise EditApplyError(f"{e.path}: file does not exist")
        content = target.read_text(encoding="utf-8")  # universal newlines -> LF
        if content.count(e.search) != 1:
            raise EditApplyError(
                f"{e.path}: SEARCH text must match exactly once (found {content.count(e.search)})")
        target.write_text(content.replace(e.search, e.replace), encoding="utf-8", newline="\n")


def make_patch(before_dir: Path, after_dir: Path) -> str:
    before_dir, after_dir = Path(before_dir), Path(after_dir)
    chunks = []
    for f in sorted((after_dir / "app").rglob("*.py")):
        rel = f.relative_to(after_dir).as_posix()
        old_file = before_dir / rel
        old = old_file.read_text(encoding="utf-8").splitlines(keepends=True) if old_file.exists() else []
        new = f.read_text(encoding="utf-8").splitlines(keepends=True)
        if old != new:
            chunks.extend(difflib.unified_diff(old, new, f"a/{rel}", f"b/{rel}"))
    return "".join(chunks)


def _source_listing(app_dir: Path) -> str:
    parts = []
    for f in sorted((app_dir / "app").rglob("*.py")):
        if f.stat().st_size:
            parts.append(f"--- {f.relative_to(app_dir).as_posix()} ---\n{f.read_text(encoding='utf-8')}")
    return "\n".join(parts)


def run_blue(llm, live_dir: Path, seed_db: Path, exploit: Exploit, logs: str, tests_dir: Path,
             ports: PortAllocator, work_root: Path, emit, max_attempts: int = 3,
             app_module: str = "app.main:app", extra_paths: list | None = None) -> BlueResult:
    live_dir = Path(live_dir)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": (
            f"Exploit that leaked {exploit.flag} ({exploit.vuln_class}):\n"
            f"{exploit.method} {exploit.path} params={exploit.params} json={exploit.json} "
            f"headers={exploit.headers}\n\nRecent log lines:\n{logs or '(none)'}\n\n"
            f"Source files:\n{_source_listing(live_dir)}")},
    ]
    for attempt in range(1, max_attempts + 1):
        reply = llm.chat(messages)
        text = reply.get("content") or ""
        emit({"type": "blue_thinking", "text": text[:1500]})
        messages.append({"role": "assistant", "content": text})
        failure = None
        staging = TargetProcess(live_dir, seed_db, ports.next(), work_root, app_module, extra_paths)
        try:
            edits = parse_edits(text)
            if not edits:
                raise EditApplyError("no SEARCH/REPLACE blocks found in your reply")
            staging.prepare()
            apply_edits(staging.dir, edits)
            staging.start()
            verdict = verify_patch(staging, exploit, tests_dir)
            if verdict.ok:
                emit({"type": "blue_attempt", "n": attempt, "ok": True, "reason": "verified"})
                return BlueResult(True, make_patch(live_dir, staging.dir), staging, attempt)
            if verdict.replay_flag_found:
                failure = "the exploit still returns the flag"
            else:
                failure = f"{verdict.tests.failed} functional test(s) failed:\n{verdict.tests.output}"
        except (EditApplyError, TargetBootError) as exc:
            failure = str(exc)
        staging.stop()
        emit({"type": "blue_attempt", "n": attempt, "ok": False, "reason": failure[:300]})
        messages.append({"role": "user", "content": f"Your patch was rejected: {failure}\nTry again."})
    return BlueResult(False, "", None, max_attempts)
