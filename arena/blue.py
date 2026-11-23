"""Blue agent: asks the LLM for SEARCH/REPLACE edits, verifies them on a staging copy."""
import difflib
import hashlib
import json
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

# Always shown: the request path usually runs through auth and the router.
SHARED_FILES = ("app/main.py", "app/db.py", "app/routes/auth.py")

RECIPES = {
    "sqli": (
        "Recipe (SQL injection): stop building SQL with f-strings. Pass values as query "
        "parameters, e.g. conn.execute(\"SELECT ... WHERE name LIKE ?\", ('%' + q + '%',)). "
        "Keep the same response shape and keep hidden = 0."
    ),
    "idor": (
        "Recipe (IDOR): scope the lookup to the logged-in user. Call current_user(authorization) "
        "and add AND owner_id = ? with user[\"id\"] to the WHERE clause. Keep the 404 for "
        "missing rows."
    ),
    "admin_bypass": (
        "Recipe (admin bypass): after current_user(authorization), require the admin role before "
        "returning anything, e.g. assert user[\"role\"] == \"admin\", \"admin only\". Admins must "
        "still get the same response."
    ),
    "path_traversal": (
        "Recipe (path traversal): resolve the requested path against the base directory and refuse "
        "anything outside it, e.g. base = Path(\"files\").resolve(); "
        "path = (base / name).resolve(); if base not in path.parents: "
        "raise HTTPException(404, \"not found\")."
    ),
}

EDIT_RE = re.compile(
    r"FILE:\s*[`*]*([^\s`*]+)[`*]*\s*\n<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)>>>>>>> REPLACE", re.S)

CACHE_VERSION = 1


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
    cached: bool = False


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


def _route_key(path: str) -> str:
    parts = [p for p in path.split("?")[0].split("/") if p]
    if parts and re.fullmatch(r"\d+", parts[-1]):
        parts.pop()
    return "/" + "/".join(parts)


def relevant_files(app_dir: Path, exploit: Exploit) -> list[Path]:
    """Only send the files a fix can plausibly touch, so Blue spends fewer tokens reading."""
    app_dir = Path(app_dir)
    all_files = sorted((app_dir / "app").rglob("*.py"))
    key = _route_key(exploit.path)
    hint = key.rsplit("/", 1)[-1].lower()
    picked = []
    for f in all_files:
        rel = f.relative_to(app_dir).as_posix().lower()
        if key in f.read_text(encoding="utf-8") or hint in f.stem.lower() or hint in rel:
            picked.append(f)
    if not picked:
        return all_files
    out, seen = [], set()
    for f in [app_dir / rel for rel in SHARED_FILES] + picked:
        if f.is_file() and f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _source_listing(app_dir: Path, files: list[Path] | None = None) -> str:
    app_dir = Path(app_dir)
    if files is None:
        files = sorted((app_dir / "app").rglob("*.py"))
    parts = []
    for f in files:
        f = Path(f)
        if f.stat().st_size:
            parts.append(f"--- {f.relative_to(app_dir).as_posix()} ---\n{f.read_text(encoding='utf-8')}")
    return "\n".join(parts)


def cache_key(exploit: Exploit) -> str:
    """A fix is reusable per bug class + route, regardless of which token or payload found it."""
    seed = json.dumps({"version": CACHE_VERSION, "method": exploit.method.upper(),
                       "route": _route_key(exploit.path), "vuln_class": exploit.vuln_class},
                      sort_keys=True)
    return hashlib.sha256(seed.encode()).hexdigest()


def _read_cache(path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if data.get("version") == CACHE_VERSION else {}


def cached_edits(path, exploit: Exploit) -> list[Edit] | None:
    if not path:
        return None
    entry = (_read_cache(path).get("patches") or {}).get(cache_key(exploit))
    if not entry:
        return None
    return [Edit(e["path"], e["search"], e["replace"]) for e in entry.get("edits", [])]


def store_edits(path, exploit: Exploit, edits: list[Edit]) -> None:
    if not path:
        return
    data = _read_cache(path) or {"version": CACHE_VERSION, "patches": {}}
    data.setdefault("patches", {})[cache_key(exploit)] = {
        "vuln_class": exploit.vuln_class,
        "route": _route_key(exploit.path),
        "edits": [{"path": e.path, "search": e.search, "replace": e.replace} for e in edits],
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def drop_cached(path, exploit: Exploit) -> None:
    if not path or not Path(path).is_file():
        return
    data = _read_cache(path)
    if (data.get("patches") or {}).pop(cache_key(exploit), None) is None:
        return
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _stage_and_verify(edits, live_dir, seed_db, exploit, tests_dir, ports, work_root, emit,
                      app_module, extra_paths) -> tuple[BlueResult | None, str | None]:
    staging = TargetProcess(live_dir, seed_db, ports.next(), work_root, app_module, extra_paths)
    keep = False
    try:
        staging.prepare()
        apply_edits(staging.dir, edits)
        staging.start()
        verdict = verify_patch(staging, exploit, tests_dir)
        if verdict.ok:
            keep = True
            return BlueResult(True, make_patch(live_dir, staging.dir), staging, 0), None
        if verdict.replay_flag_found:
            return None, "the exploit still returns the flag"
        return None, f"{verdict.tests.failed} functional test(s) failed:\n{verdict.tests.output}"
    except (EditApplyError, TargetBootError) as exc:
        return None, str(exc)
    finally:
        if not keep:
            staging.stop()


def run_blue(llm, live_dir: Path, seed_db: Path, exploit: Exploit, logs: str, tests_dir: Path,
             ports: PortAllocator, work_root: Path, emit, max_attempts: int = 3,
             app_module: str = "app.main:app", extra_paths: list | None = None,
             cache_path: Path | None = None) -> BlueResult:
    live_dir = Path(live_dir)
    files = relevant_files(live_dir, exploit)
    recipe = RECIPES.get(exploit.vuln_class)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": (
            f"Exploit that leaked {exploit.flag} ({exploit.vuln_class}):\n"
            f"{exploit.method} {exploit.path} params={exploit.params} json={exploit.json} "
            f"headers={exploit.headers}\n\nRecent log lines:\n{(logs or '(none)')[-1200:]}\n\n"
            f"{recipe + chr(10) + chr(10) if recipe else ''}"
            f"Source files involved:\n{_source_listing(live_dir, files)}")},
    ]
    cached = cached_edits(cache_path, exploit)
    if cached:
        result, _ = _stage_and_verify(cached, live_dir, seed_db, exploit, tests_dir, ports,
                                      work_root, emit, app_module, extra_paths)
        if result:
            emit({"type": "blue_cache", "hit": True, "edits": len(cached)})
            result.cached = True
            return result
        drop_cached(cache_path, exploit)
        emit({"type": "blue_cache", "hit": False, "reason": "cached fix no longer verifies"})
    for attempt in range(1, max_attempts + 1):
        reply = llm.chat(messages)
        text = reply.get("content") or ""
        emit({"type": "blue_thinking", "text": text[:1500]})
        messages.append({"role": "assistant", "content": text})
        edits = parse_edits(text)
        if not edits:
            failure = "no SEARCH/REPLACE blocks found in your reply"
            emit({"type": "blue_attempt", "n": attempt, "ok": False, "reason": failure})
            messages.append({"role": "user", "content": f"Your patch was rejected: {failure}\nTry again."})
            continue
        result, failure = _stage_and_verify(edits, live_dir, seed_db, exploit, tests_dir, ports,
                                            work_root, emit, app_module, extra_paths)
        if result:
            emit({"type": "blue_attempt", "n": attempt, "ok": True, "reason": "verified"})
            store_edits(cache_path, exploit, edits)
            result.attempts = attempt
            return result
        emit({"type": "blue_attempt", "n": attempt, "ok": False, "reason": failure[:300]})
        messages.append({"role": "user", "content": f"Your patch was rejected: {failure}\nTry again."})
    return BlueResult(False, "", None, max_attempts)
