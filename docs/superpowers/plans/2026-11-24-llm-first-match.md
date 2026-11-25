# LLM-first Match Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a default match LLM-driven (Red discovers, Blue diagnoses then patches), keeping the deterministic sweep + verified cache only behind `--demo`.

**Architecture:** `arena.yaml`/`ArenaConfig` default to `strategy: llm`; the orchestrator skips `Sweep` and the cache unless the strategy is `hybrid`/`sweep` or `--demo` is passed. Red keeps its tool-calling loop with a 7-class playbook, a compact findings reminder, and a 6-turn history window. Blue gains a diagnosis model call whose parsed `blue_diagnosis` event is logged and shown in the UI; the patch call then receives only the diagnosed file. Each verified patch is exported immediately.

**Tech Stack:** Python 3.11, FastAPI orchestrator, pytest, React 19 + Vite + Tailwind (SOC UI), FreeLLM OpenAI-compatible router.

**Spec:** `docs/superpowers/specs/2026-11-24-llm-first-match-design.md`

## Global Constraints

- Never read, print, or commit `.env` or any API key. The router key stays in the environment.
- Do not create git commits unless Sidaarth explicitly asks; replace every commit step with a test checkpoint.
- All attack traffic stays on localhost/sandbox (enforced by `arena/httptool.py` host lock).
- Deterministic templates must stay labelled as templates/scripted (UI `source === 'sweep' ? 'template' : 'model'`).
- UI numbers come from event logs; render `—` when a value was not recorded. No fabricated data.
- `fixtures/dev_target` is "representative of common AI-generated bugs", never "unedited AI output".
- `--replay` stays the zero-API-key path for judges.

---

### Task 1: Default to LLM, add `--demo`, gate sweep/cache, export per patch

**Files:**
- Modify: `vibe-arena/arena/config.py:19` (default strategy), `vibe-arena/arena.yaml:19`
- Modify: `vibe-arena/arena/cli.py:13-51,66-77`
- Modify: `vibe-arena/arena/orchestrator.py:39-62,104-131`
- Test: `vibe-arena/tests/test_config.py`, `vibe-arena/tests/test_orchestrator.py`

**Interfaces:**
- Consumes: `load_config`, `run_match(...)`
- Produces: `run_match(..., reuse_cache: bool | None = None)`; `ArenaConfig.strategy` defaults to `"llm"`.

- [ ] **Step 1: Update the config tests to the new default**

In `tests/test_config.py`, change both expectations from `"hybrid"` to `"llm"`:

```python
def test_strategy_loot_and_cache_defaults():
    cfg = load_config(str(ROOT / "arena.yaml"))
    assert cfg.strategy == "llm"
    assert cfg.loot_paths == ["secret.txt"]
    assert cfg.cache_path == (ROOT / "patches" / "cache.json").resolve()


def test_loot_paths_derived_from_extra_paths_when_absent(tmp_path):
    cfg_file = tmp_path / "arena.yaml"
    cfg_file.write_text(
        "app_dir: app\nseed_db: seed.db\nfunctional_tests: tests\n"
        "extra_paths: [uploads, notes.txt, .env]\n",
        encoding="utf-8",
    )
    cfg = load_config(str(cfg_file))
    assert cfg.loot_paths == ["notes.txt", ".env"]
    assert cfg.strategy == "llm"
    assert cfg.cache_path is None
```

- [ ] **Step 2: Run the config tests to verify they fail**

Run: `.venv\Scripts\python -m pytest tests/test_config.py -q`
Expected: 2 failures (`hybrid` != `llm`).

- [ ] **Step 3: Change the defaults**

`arena/config.py` line 19 and the `load_config` fallbacks:

```python
    strategy: str = "llm"
```
```python
    strategy = raw.get("strategy", "llm")
```
```python
        strategy=raw.get("strategy", "llm"),
```

`arena.yaml` line 19: `strategy: llm`

- [ ] **Step 4: Add `--demo` and the reuse-cache switch**

In `arena/cli.py` `cmd_run`, before `run_match`:

```python
    if a.demo and not a.strategy:
        cfg.strategy = "hybrid"  # the offline demo: sweep first, then cache
```
and the call:

```python
    s = run_match(cfg, red, blue, log, rounds=a.rounds, work_root=work,
                  out_dir=Path("matches") / match_id, explore=a.explore,
                  reuse_cache=True if a.demo else None)
```
Arguments in `main()`:

```python
    r.add_argument("--rounds", type=int, default=2)
    r.add_argument("--demo", action="store_true",
                   help="deterministic sweep + verified-patch cache (offline demo)")
```

In `arena/orchestrator.py`:

```python
def run_match(cfg, llm_red, llm_blue, log: EventLog, rounds: int = 2, work_root: Path = Path("work"),
              out_dir: Path = Path("matches/last"), base_port: int = 8001,
              strategy: str | None = None, explore: bool = False,
              cache_path: Path | None = None, reuse_cache: bool | None = None) -> MatchSummary:
    emit = log.emit
    strategy = strategy or cfg.strategy
    if reuse_cache is None:
        reuse_cache = strategy in ("hybrid", "sweep")
    cache_path = cfg.cache_path if cache_path is None else cache_path
    if not reuse_cache:
        cache_path = None
```

- [ ] **Step 5: Export after every verified patch**

In the patch-success block, after the second `score` emit and before the health re-run:

```python
                    emit({"type": "score", "red": summary.red, "blue": summary.blue})
                    export(out_dir, exploits_closed, patches, ttps)  # never lose earlier fixes
                    h = run_functional_tests(cfg.functional_tests, live.url)
```

- [ ] **Step 6: Add the demo test and the default-LLM test**

Append to `tests/test_orchestrator.py`:

```python
def test_default_llm_match_never_runs_the_sweep(tmp_path):
    red = FakeLLM([
        tc("send_http_request", {"method": "POST", "path": "/api/login",
                                 "json": {"username": "alice", "password": "alice123"}}),
        tc("send_http_request", {"method": "GET", "path": "/api/invoices/3",
                                 "headers": {"Authorization": "Bearer tok-1"}}),
    ])
    blue = FakeLLM([
        {"content": "FILE: app/routes/invoices.py\nFUNCTION: get_invoice\nLINES: 14-17\n"
                    "ROOT CAUSE: owner_id is never checked\nREACHED BY: GET /api/invoices/3\n",
         "tool_calls": []},
        {"content": block(SEARCH, FIX), "tool_calls": []},
    ])
    log = EventLog(tmp_path / "events.jsonl")
    summary = run_match(CFG, red, blue, log, rounds=1, work_root=tmp_path / "work",
                        out_dir=tmp_path / "out", base_port=9960, strategy="llm")
    types = [e["type"] for e in log.events]
    assert "sweep_start" not in types and "sweep_done" not in types
    assert summary.sweep_requests == 0 and summary.sweep_findings == 0
    assert summary.red_llm_calls == red.calls >= 1
    assert summary.blue_llm_calls == blue.calls == 2  # diagnosis + patch
    assert summary.cache_hits == 0 and types.count("patched") == 1
    assert not ALLOWED_PORTS


def test_each_verified_patch_is_exported_immediately(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr("arena.orchestrator.export",
                        lambda out, ex, pa, tt: calls.append(len(pa)))
    red = FakeLLM([
        tc("send_http_request", {"method": "GET", "path": "/api/invoices/3",
                                 "headers": {"Authorization": "Bearer tok-1"}}),
    ])
    blue = FakeLLM([
        {"content": "FILE: app/routes/invoices.py\nROOT CAUSE: missing owner check\n",
         "tool_calls": []},
        {"content": block(SEARCH, FIX), "tool_calls": []},
    ])
    log = EventLog(tmp_path / "events.jsonl")
    run_match(CFG, red, blue, log, rounds=1, work_root=tmp_path / "work",
              out_dir=tmp_path / "out", base_port=9965, strategy="llm")
    assert calls[0] == 1  # exported right after the first verified patch
```

- [ ] **Step 7: Run the task tests**

Run: `.venv\Scripts\python -m pytest tests/test_config.py tests/test_orchestrator.py -q`
Expected: config passes; orchestrator tests that still use one-reply Blue scripts fail (they are updated in Task 5).

Checkpoint: do not commit.

---

### Task 2: Red — seven-class discovery, findings reminder, bounded context

**Files:**
- Modify: `vibe-arena/arena/red.py:11-21,42-52,78-117,148-170`
- Test: `vibe-arena/tests/test_red.py`

**Interfaces:**
- Produces: `classify(path, params=None, method="GET", json_body=None) -> str`; `run_red(..., max_steps: int = 30)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_red.py`:

```python
def test_classify_recognizes_all_seven_classes():
    from arena.red import classify
    assert classify("/api/search", {"q": "' OR 1=1--"}) == "sqli"
    assert classify("/api/invoices/3") == "idor"
    assert classify("/api/admin/export") == "admin_bypass"
    assert classify("/api/files", {"name": "../secret.txt"}) == "path_traversal"
    assert classify("/api/profile", None, "PUT", {"role": "admin"}) == "mass_assignment"
    assert classify("/api/debug/config") == "debug_exposure"
    assert classify("/api/calc", {"expr": "1+1"}) == "code_injection"


def test_red_breach_events_are_marked_as_model_driven(tmp_path):
    t = target(tmp_path, PortAllocator(9670).next())
    events = []
    try:
        llm = FakeLLM([
            tc("send_http_request", {"method": "GET", "path": "/api/search",
                                     "params": {"q": "' OR 1=1--"}}),
        ])
        run_red(llm, t.url, {"paths": {}}, USERS, events.append, max_steps=3)
    finally:
        t.stop()
    breach = [e for e in events if e["type"] == "breach"]
    assert breach and breach[0]["source"] == "llm"


def test_red_reminds_the_model_what_it_already_found(tmp_path):
    t = target(tmp_path, PortAllocator(9680).next())
    try:
        llm = FakeLLM([
            tc("send_http_request", {"method": "GET", "path": "/api/search",
                                     "params": {"q": "' OR 1=1--"}}),
            tc("discover_routes", {}),
        ])
        run_red(llm, t.url, {"paths": {}}, USERS, lambda e: None, max_steps=3)
    finally:
        t.stop()
    followup = llm.seen[-1]
    text = " ".join(m.get("content") or "" for m in followup)
    assert "Findings so far" in text and "sqli /api/search" in text
    # the reminder is a fresh short message, not replayed history
    assert len(followup) <= 2 + 1 + 2
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv\Scripts\python -m pytest tests/test_red.py -q -k "classify or model_driven or reminds"`
Expected: FAIL (`classify` has no `method` parameter; `source` missing; no reminder).

- [ ] **Step 3: Implement**

`SYSTEM` becomes:

```python
SYSTEM = (
    "You are the Red agent in a local security exercise. You are attacking a small web API that "
    "its owner runs in an isolated sandbox on this machine, with permission. Your goal is to "
    "find hidden canary strings that look like FLAG{...}. Work systematically: call "
    "discover_routes, log in with the test accounts you are given, then test EVERY class: SQL "
    "injection on query params, IDOR by requesting other users' ids, admin routes as a normal "
    "user, path traversal on file/name params, mass assignment by sending role/is_admin in "
    "PUT/PATCH bodies, unauthenticated debug/diagnostic routes, and eval-style expression "
    "params. get_payload_templates gives payload ideas when you are unsure. Do not repeat a "
    "class/route listed under Findings so far; move to the next untested class. Stop when you "
    "have tried every class on every route or run out of ideas."
)
```

Tool description:

```python
        "description": "Payload ideas for one class: sqli, idor, admin_bypass, path_traversal, "
                       "mass_assignment, debug_exposure, code_injection.",
```

`classify`:

```python
def classify(path: str, params: dict | None = None, method: str = "GET",
             json_body: dict | None = None) -> str:
    text = " ".join([path, json.dumps(params or {}), json.dumps(json_body or {})])
    if "admin" in path:
        return "admin_bypass"
    if ".." in text:
        return "path_traversal"
    if re.search(r"'|--|\bOR\b|UNION", text, re.I):
        return "sqli"
    if method.upper() in ("PUT", "PATCH") and re.search(r"role|is_admin", text, re.I):
        return "mass_assignment"
    if re.search(r"debug|diagnostic", path, re.I):
        return "debug_exposure"
    if re.search(r"expr|expression|eval|code|cmd|command", text, re.I):
        return "code_injection"
    if re.search(r"/\d+", path):
        return "idor"
    return "unknown"
```

Findings reminder helper (above `run_red`):

```python
def _findings_line(found: dict[str, Exploit]) -> str:
    seen = "; ".join(f"{ex.vuln_class} {normalize_route(ex.path)}" for ex in found.values())
    return (f"Findings so far (do NOT repeat these classes/routes): {seen}. "
            "Move to an untested class.")
```

Inside the `for _ in range(max_steps)` loop, replace the message assembly with:

```python
        messages = list(preamble)
        if found:
            messages.append({"role": "user", "content": _findings_line(found)})
        for group in history[-keep_steps:]:
            messages.extend(group)
```

Change the signature default and the Exploit construction:

```python
def run_red(llm, base_url: str, openapi: dict, users: list, emit, max_steps: int = 30,
```
```python
            ex = Exploit(args.get("method", "GET"), path, args.get("headers"), args.get("params"),
                         args.get("json"), flag,
                         classify(path, args.get("params"), args.get("method", "GET"),
                                  args.get("json")), login)
            found[flag] = ex
            emit({"type": "breach", "source": "llm", "route": normalize_route(path),
```

- [ ] **Step 4: Run the red tests**

Run: `.venv\Scripts\python -m pytest tests/test_red.py -q`
Expected: all pass, including the untouched history-window test (`len(last) == 2 + 2 * 2` still holds because nothing was found there).

Checkpoint: no commit.

---

### Task 3: Blue diagnosis parser

**Files:**
- Modify: `vibe-arena/arena/blue.py` (new regex + `parse_diagnosis`)
- Test: `vibe-arena/tests/test_blue.py`

**Interfaces:**
- Produces: `parse_diagnosis(text: str) -> dict` with keys `file`, `function`, `lines`, `root_cause`, `reached_by` (always present; empty string when absent).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_blue.py`:

```python
def test_parse_diagnosis_reads_every_field():
    from arena.blue import parse_diagnosis
    text = ("FILE: app/routes/invoices.py\nFUNCTION: get_invoice\nLINES: 14-17\n"
            "ROOT CAUSE: the query never filters by owner_id\n"
            "REACHED BY: GET /api/invoices/3\n")
    d = parse_diagnosis(text)
    assert d["file"] == "app/routes/invoices.py"
    assert d["function"] == "get_invoice"
    assert d["lines"] == "14-17"
    assert d["root_cause"] == "the query never filters by owner_id"
    assert d["reached_by"] == "GET /api/invoices/3"


def test_parse_diagnosis_keeps_raw_text_when_the_format_is_missing():
    from arena.blue import parse_diagnosis
    d = parse_diagnosis("I believe the invoice lookup forgets the owner check.")
    assert d["file"] == "" and d["function"] == ""
    assert d["root_cause"] == "I believe the invoice lookup forgets the owner check."
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv\Scripts\python -m pytest tests/test_blue.py -q -k diagnosis`
Expected: FAIL (name cannot be imported).

- [ ] **Step 3: Implement the parser**

Add near `EDIT_RE` in `arena/blue.py`:

```python
DIAGNOSIS_SYSTEM = (
    "You are the Blue agent. Phase 1 of 2: locate the defect the exploit below reached. "
    "Read the source, find the exact handler and lines, and explain why the request works. "
    "Do not write a patch yet. Reply only in this exact format:\n"
    "FILE: app/routes/example.py\n"
    "FUNCTION: handler_name\n"
    "LINES: 12-18\n"
    "ROOT CAUSE: one or two sentences\n"
    "REACHED BY: METHOD /path with the payload\n"
)

_DIAG_RE = re.compile(r"(?m)^\s*(FILE|FUNCTION|LINES|ROOT CAUSE|REACHED BY)\s*:\s*(.*)$")
_DIAG_KEYS = {"FILE": "file", "FUNCTION": "function", "LINES": "lines",
              "ROOT CAUSE": "root_cause", "REACHED BY": "reached_by"}


def parse_diagnosis(text: str) -> dict:
    out = {"file": "", "function": "", "lines": "", "root_cause": "", "reached_by": ""}
    for key, value in _DIAG_RE.findall(text or ""):
        out[_DIAG_KEYS[key]] = value.strip()
    if not any(out.values()):
        out["root_cause"] = (text or "").strip()[:500]
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv\Scripts\python -m pytest tests/test_blue.py -q -k diagnosis`
Expected: 2 passed.

Checkpoint: no commit.

---

### Task 4: Blue two-phase run — diagnosis call, single-file patch prompt, fallback

**Files:**
- Modify: `vibe-arena/arena/blue.py:86-99` (`BlueResult`), `blue.py:253-321` (`run_blue`)
- Test: `vibe-arena/tests/test_blue.py`

**Interfaces:**
- Consumes: `parse_diagnosis`, `DIAGNOSIS_SYSTEM`
- Produces: `BlueResult.diagnosis: dict | None`; `run_blue(...)` emits `blue_diagnosis` before `blue_attempt`.

- [ ] **Step 1: Update the Blue tests for two-phase (write the failing tests)**

Add a shared diagnosis fixture near `IDOR`:

```python
DIAG = ("FILE: app/routes/invoices.py\nFUNCTION: get_invoice\nLINES: 14-17\n"
        "ROOT CAUSE: the query never filters by owner_id\nREACHED BY: GET /api/invoices/3\n")
```

Replace the script in `test_blue_end_to_end_accepts_fix` and add the new assertions:

```python
        llm = FakeLLM([{"content": DIAG, "tool_calls": []},
                       {"content": block(SEARCH, FIX), "tool_calls": []}])
        res = run_blue(llm, live.dir, CFG.seed_db, IDOR, "", CFG.functional_tests,
                       PortAllocator(9721), tmp_path, events.append, extra_paths=CFG.extra_paths)
        assert res.ok and res.attempts == 1 and res.new_target.port != live.port
        assert not res.cached and res.diagnosis["file"] == "app/routes/invoices.py"
        assert "owner_id" in res.patch and "--- a/app/routes/invoices.py" in res.patch
        assert "Recipe (IDOR)" in llm.seen[0][1]["content"]
        patch_prompt = llm.seen[1][1]["content"]
        assert "--- app/routes/invoices.py ---" in patch_prompt
        assert "--- app/routes/auth.py ---" not in patch_prompt  # only the located file
        res.new_target.stop()
    finally:
        live.stop()
    kinds = [e["type"] for e in events]
    assert kinds.index("blue_diagnosis") < kinds.index("blue_attempt")
```

Update retries:

```python
        bad = {"content": block("this text is not in the file", "x"), "tool_calls": []}
        llm = FakeLLM([{"content": DIAG, "tool_calls": []}, bad, bad, bad])
        res = run_blue(...)
        assert not res.ok and res.attempts == 3 and llm.calls == 4
```

Update the stale-cache test script and call count:

```python
        llm = FakeLLM([{"content": DIAG, "tool_calls": []},
                       {"content": block(SEARCH, FIX), "tool_calls": []}])
        ...
        assert res.ok and not res.cached and llm.calls == 2
```

Update the unexpected-verification-error script:

```python
        llm = FakeLLM([{"content": DIAG, "tool_calls": []},
                       {"content": block(SEARCH, FIX), "tool_calls": []}])
```

Add the fallback tests:

```python
def test_diagnosis_provider_failure_falls_back_to_single_phase(tmp_path):
    live = TargetProcess(CFG.app_dir, CFG.seed_db, 9780, tmp_path, extra_paths=CFG.extra_paths)
    live.prepare(); live.start()
    events = []
    try:
        llm = FakeLLM([RuntimeError("all models failed: 503"),
                       {"content": block(SEARCH, FIX), "tool_calls": []}])
        res = run_blue(llm, live.dir, CFG.seed_db, IDOR, "", CFG.functional_tests,
                       PortAllocator(9781), tmp_path, events.append, extra_paths=CFG.extra_paths)
        assert res.ok and res.diagnosis is None
        assert any(e["type"] == "blue_error" and "diagnosis" in e["error"] for e in events)
        assert "--- app/routes/auth.py ---" in llm.seen[1][1]["content"]  # full fallback set
        res.new_target.stop()
    finally:
        live.stop()


def test_diagnosis_file_outside_app_is_ignored(tmp_path):
    from arena.blue import _diagnose_file
    (tmp_path / "app").mkdir()
    assert _diagnose_file(tmp_path, {"file": "../evil.py"}) is None
    assert _diagnose_file(tmp_path, {"file": "app/missing.py"}) is None
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv\Scripts\python -m pytest tests/test_blue.py -q -k "end_to_end or diagnosis or stale or retries or unexpected"`
Expected: FAIL (diagnosis reply consumed by the patch parser; no `blue_diagnosis`).

- [ ] **Step 3: Implement diagnosis + narrowing + fallback**

Add imports at the top of `arena/blue.py`:

```python
from arena.discover import normalize_route
from arena.llm import BudgetExceeded
```

`BlueResult` gains a field:

```python
@dataclass
class BlueResult:
    ok: bool
    patch: str
    new_target: TargetProcess | None
    attempts: int
    cached: bool = False
    diagnosis: dict | None = None
```

New helpers above `_stage_and_verify`:

```python
def _diagnose_file(live_dir: Path, diagnosis: dict) -> list[Path] | None:
    raw = (diagnosis.get("file") or "").strip().strip("`* ")
    if not raw:
        return None
    app_root = (Path(live_dir) / "app").resolve()
    candidate = (Path(live_dir) / raw).resolve()
    if candidate.suffix == ".py" and candidate.is_file() and candidate.is_relative_to(app_root):
        return [candidate]
    return None


def _diagnose(llm, live_dir: Path, exploit: Exploit, files: list[Path], recipe: str | None,
              emit) -> dict | None:
    prompt = (
        f"Exploit that leaked {exploit.flag} ({exploit.vuln_class}):\n"
        f"{exploit.method} {exploit.path} params={exploit.params} json={exploit.json} "
        f"headers={exploit.headers}\n\n"
        f"{recipe + chr(10) + chr(10) if recipe else ''}"
        f"Source files involved:\n{_source_listing(live_dir, files)}")
    try:
        reply = llm.chat([{"role": "system", "content": DIAGNOSIS_SYSTEM},
                          {"role": "user", "content": prompt}])
    except BudgetExceeded:
        raise
    except RuntimeError as exc:
        emit({"type": "blue_error", "error": f"diagnosis: {exc}"})
        return None
    diagnosis = parse_diagnosis(reply.get("content") or "")
    emit({"type": "blue_diagnosis", "vuln_class": exploit.vuln_class,
          "route": normalize_route(exploit.path), **diagnosis})
    return diagnosis
```

In `run_blue`, after the cache block and before the `messages = [...]` construction:

```python
    diagnosis = _diagnose(llm, live_dir, exploit, files, recipe, emit)
    patch_files = (_diagnose_file(live_dir, diagnosis) if diagnosis else None) or files
    diag_text = ""
    if diagnosis:
        diag_text = ("Diagnosis from your own analysis:\n"
                     f"FILE: {diagnosis['file']}\nFUNCTION: {diagnosis['function']}\n"
                     f"LINES: {diagnosis['lines']}\n"
                     f"ROOT CAUSE: {diagnosis['root_cause']}\n"
                     f"REACHED BY: {diagnosis['reached_by']}\n\n")
```

and change the user message's tail to:

```python
            f"{recipe + chr(10) + chr(10) if recipe else ''}"
            f"{diag_text}"
            f"Source files involved:\n{_source_listing(live_dir, patch_files)}")},
```

Set the diagnosis on success, in both return paths of the attempt loop:

```python
        if result:
            emit({"type": "blue_attempt", "n": attempt, "ok": True, "reason": "verified"})
            store_edits(cache_path, exploit, edits)
            result.attempts = attempt
            result.diagnosis = diagnosis
            return result
```

Cache hits keep `diagnosis=None` (the fix was not re-derived).

- [ ] **Step 4: Run the Blue tests**

Run: `.venv\Scripts\python -m pytest tests/test_blue.py -q`
Expected: all pass (cache-hit test still shows 0 calls).

Checkpoint: no commit.

---

### Task 5: Orchestrator emits the diagnosis, site_api exposes it, update scripted matches

**Files:**
- Modify: `vibe-arena/arena/orchestrator.py:117-119`
- Modify: `vibe-arena/arena/site_api.py:285-315`
- Test: `vibe-arena/tests/test_orchestrator.py`, `vibe-arena/tests/test_site_api.py`

**Interfaces:**
- Consumes: `BlueResult.diagnosis`
- Produces: `patched` events include `"diagnosis": {...} | None`; `/api/patches` rows include `diagnosis`.

- [ ] **Step 1: Write the failing site_api test**

Append to `tests/test_site_api.py`:

```python
def test_patches_expose_the_blue_diagnosis_when_recorded(tmp_path):
    import json as _json
    d = tmp_path / "live-diag"
    d.mkdir()
    lines = [
        {"type": "match_start", "strategy": "llm", "seq": 1, "ts": 0},
        {"type": "breach", "vuln_class": "idor", "route": "/api/invoices/{id}",
         "flag": "FLAG{idor_invoice_leak}", "method": "GET", "path": "/api/invoices/3",
         "seq": 2, "ts": 1},
        {"type": "patched", "vuln_class": "idor", "route": "/api/invoices/{id}",
         "patch": "--- a/app/routes/invoices.py\n+++ b/app/routes/invoices.py\n",
         "ttp_seconds": 7.1,
         "diagnosis": {"file": "app/routes/invoices.py", "function": "get_invoice",
                       "lines": "14-17", "root_cause": "owner_id is not checked",
                       "reached_by": "GET /api/invoices/3"},
         "seq": 3, "ts": 8},
        {"type": "match_end", "summary": {"red": 1, "blue": 1, "closed": 1, "total": 1},
         "seq": 4, "ts": 9},
    ]
    (d / "events.jsonl").write_text("".join(_json.dumps(e) + "\n" for e in lines),
                                    encoding="utf-8")
    rows = site_api.patches(tmp_path)
    assert rows[0]["diagnosis"]["file"] == "app/routes/invoices.py"
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv\Scripts\python -m pytest tests/test_site_api.py -q -k diagnosis`
Expected: FAIL (`KeyError: 'diagnosis'`).

- [ ] **Step 3: Implement**

`orchestrator.py` patched emit:

```python
                    emit({"type": "patched", "route": route, "vuln_class": ex.vuln_class,
                          "cached": res.cached, "patch": res.patch, "ttp_seconds": ttp,
                          "diagnosis": res.diagnosis})
```

`site_api.py` `patches()` row:

```python
            "referee_notes": f"Patch verified in {e.get('ttp_seconds')}s"
                             + (" (cached)" if e.get("cached") else ""),
            "diagnosis": e.get("diagnosis"),
            "match_id": latest["id"],
```

- [ ] **Step 4: Update every scripted Blue LLM in the orchestrator tests**

In `tests/test_orchestrator.py`, each `blue = FakeLLM([...])` that feeds real matches needs a diagnosis reply before each patch reply. Add at module level:

```python
DIAG = ("FILE: app/routes/invoices.py\nFUNCTION: get_invoice\nLINES: 14-17\n"
        "ROOT CAUSE: the query never filters by owner_id\nREACHED BY: GET /api/invoices/3\n")
```

- `test_run_match_with_fakes`: `blue = FakeLLM([{"content": DIAG, "tool_calls": []}, {"content": block(SEARCH, FIX), "tool_calls": []}])`.
- `test_sweep_match_closes_all_seven_bugs_with_zero_red_tokens`: interleave seven diagnosis replies (the exact FILE for each class) before each patch. Build it literally:

```python
DIAGS = {
    "sqli": "FILE: app/routes/search.py\nROOT CAUSE: f-string SQL\n",
    "idor": "FILE: app/routes/invoices.py\nROOT CAUSE: no owner check\n",
    "admin_bypass": "FILE: app/routes/admin.py\nROOT CAUSE: no role check\n",
    "path_traversal": "FILE: app/routes/files.py\nROOT CAUSE: uncanonicalised join\n",
    "mass_assignment": "FILE: app/routes/profile.py\nROOT CAUSE: role copied from body\n",
    "debug_exposure": "FILE: app/routes/debug.py\nROOT CAUSE: unauthenticated debug route\n",
    "code_injection": "FILE: app/routes/calc.py\nROOT CAUSE: eval on user input\n",
}
PATCHES = {
    "sqli": block(SQL_OLD, SQL_FIX, "app/routes/search.py"),
    "idor": block(SEARCH, FIX),
    "admin_bypass": block(ADMIN_OLD, ADMIN_FIX, "app/routes/admin.py"),
    "path_traversal": block(TRAV_OLD, TRAV_FIX, "app/routes/files.py"),
    "mass_assignment": block(PROFILE_OLD, PROFILE_FIX, "app/routes/profile.py"),
    "debug_exposure": block(DEBUG_OLD, DEBUG_FIX, "app/routes/debug.py"),
    "code_injection": block(CALC_OLD, CALC_FIX, "app/routes/calc.py"),
}
```

  Important: the diagnosis reply must name the same file as the patch, because the patch prompt now narrows to it. Note `block(SEARCH, FIX)` defaults to `app/routes/invoices.py`, so the sqli patch must use `block(SQL_OLD, SQL_FIX, "app/routes/search.py")`.
  Build the script in discovery order:

```python
    blue = FakeLLM([item for cls in ("sqli", "idor", "admin_bypass", "path_traversal",
                                     "mass_assignment", "debug_exposure", "code_injection")
                    for item in ({"content": DIAGS[cls], "tool_calls": []},
                                 {"content": PATCHES[cls], "tool_calls": []})])
```

  Update assertions: `summary.llm_calls == blue.calls == 14`, `summary.blue_llm_calls == blue.calls == 14`, `summary.blue_tokens == 0`, `types.count("blue_diagnosis") == 7`.
- `test_hybrid_skips_the_red_llm_when_the_sweep_finds_bugs`: same interleaved script and the same call-count update.
- `test_blue_provider_outage...`: add one `RuntimeError("all models failed: m: 429")` for the diagnosis call before the same error for the patch (two entries total). `blue_error` is still emitted.
- `test_red_budget_exhaustion...` and `test_budget_exhaustion...` keep `FakeLLM([])` / `[BudgetExceeded(...)]`; the diagnosis call consumes the first scripted item, which is still the intended failure.
- `test_red_budget_exhaustion...` currently expects `summary.red == 0` — unchanged.

- [ ] **Step 5: Run the affected tests**

Run: `.venv\Scripts\python -m pytest tests/test_site_api.py tests/test_orchestrator.py -q -k "not sample"`
Expected: pass.

Checkpoint: no commit.

---

### Task 6: UI — diagnosis event, LOCATED panel, honest tier strip

**Files:**
- Modify: `vibe-arena/ui/src/services/api.ts:228-232`
- Modify: `vibe-arena/ui/src/pages/BattleArenaPage.tsx:254-257,373-427,565-572`

**Interfaces:**
- Consumes: raw `blue_diagnosis` events via WebSocket.

- [ ] **Step 1: Map the event in `normalizeEvent`**

Insert before the `blue_thinking` case:

```ts
    case 'blue_diagnosis':
      return {
        ...base, source: 'BLUE', event_type: 'ROOT_CAUSE_ANALYSIS', severity: 'info',
        endpoint: data.route,
        summary: `Diagnosis: ${data.file || 'file unknown'}` +
          `${data.function ? `:${data.function}` : ''}` +
          `${data.lines ? ` lines ${data.lines}` : ''} - ${data.root_cause || 'located the defect'}.`,
      };
```

- [ ] **Step 2: Add the LOCATED panel**

In `BattleArenaPage.tsx`, next to `const findingsCount = ...` add:

```tsx
  const latestDiagnosis = [...events].reverse()
    .find((e) => e.details?.type === 'blue_diagnosis')?.details;
```

Inside the Blue panel, before the "Verified Patches" block:

```tsx
            <div className="p-3 rounded-lg bg-blue-950/20 border border-blue-900/60 text-xs font-mono space-y-1 mb-4">
              <div className="text-[10px] text-blue-400 uppercase font-bold flex items-center gap-1">
                <FileCode2 className="w-3 h-3" /> Located
              </div>
              {latestDiagnosis ? (
                <>
                  <p className="text-cyan-200 break-all">
                    {latestDiagnosis.file || 'file not named'}
                    {latestDiagnosis.function ? `:${latestDiagnosis.function}` : ''}
                    {latestDiagnosis.lines ? `:${latestDiagnosis.lines}` : ''}
                  </p>
                  <p className="text-slate-400 leading-snug">{latestDiagnosis.root_cause}</p>
                </>
              ) : (
                <p className="text-slate-500">No diagnosis recorded yet.</p>
              )}
            </div>
```

- [ ] **Step 3: Make the tier strip honest**

Above the two-tier strip add:

```tsx
        const sweepUsed = (battle?.sweep_requests ?? 0) > 0;
```

Replace the Tier 1 description and badge text:

```tsx
                <div className="text-[11px] font-mono text-slate-400">
                  {sweepUsed
                    ? `${battle.sweep_requests} sweep requests · ${battle.sweep_findings} findings · ${battle.cache_hits} cached patches`
                    : 'Not used in this match (LLM-only)'}
                </div>
```
```tsx
              {battle.llm_calls === 0
                ? '0 LLM calls · 0 tokens'
                : sweepUsed
                  ? 'scripted path offline'
                  : 'bypassed: models did the work'}
```

Replace the Tier 2 description:

```tsx
                  {battle.llm_calls === 0
                    ? 'Not needed: sweep + cache closed every finding'
                    : battle.llm_calls === null
                      ? 'Older log: per-call counts were not recorded'
                      : sweepUsed
                        ? 'Used where the fast path had no answer'
                        : 'LLM discovery + diagnosis + patch'}
```

- [ ] **Step 4: Build the UI**

Run: `cd ui && npm run build`
Expected: build succeeds with no TypeScript errors.

Checkpoint: no commit.

---

### Task 7: Record the LLM-only sample and align sample-derived tests

**Files:**
- Modify (generated): `vibe-arena/matches/sample.jsonl`, `vibe-arena/matches/sample/`
- Modify: `vibe-arena/tests/test_site_api.py:20-34,51-66`, `vibe-arena/tests/test_server.py`
- Modify: `vibe-arena/README.md`, `vibe-arena/docs/TEAM_TASKS.md`

**Interfaces:**
- Consumes: a real router via environment (`ARENA_API_KEY`, `ARENA_BASE_URL` already set).
- Produces: the shipped sample is an LLM-only match with real call counts and diagnoses.

- [ ] **Step 1: Confirm the router is awake**

Run: `.venv\Scripts\python -c "from arena.llm import LLM; m=LLM('blue').chat([{'role':'user','content':'reply with the word ok'}]); print('ok' if m.get('content') else 'empty')"`
Expected: prints `ok`. If it errors, the host is offline; retry later, do not fake the sample.

- [ ] **Step 2: Record a full LLM match**

Run: `.venv\Scripts\python -m arena.cli run --rounds 3`
Expected: a `matches/live-YYYYMMDD-HHMMSS/` directory ending with `match_end`, `closed 7/7`, non-zero Red and Blue calls. If it is not 7/7, keep the partial run for evidence and rerun once; investigate a miss (missing `--rounds`, provider error, or a class the model skipped).

- [ ] **Step 3: Promote the run to the sample (preserve the old one)**

```bash
LATEST=$(ls -td matches/live-* | head -1)
mv matches/sample matches/sample.prev-demo
rm -rf matches/sample && cp -r "$LATEST" matches/sample
cp "$LATEST/events.jsonl" matches/sample.jsonl
```

Then update the sample label if needed (the server adds `sample: true` on replay, so no file edit).

- [ ] **Step 4: Read the new sample's numbers**

Run: `.venv\Scripts\python -m arena.cli replay matches/sample.jsonl | tail -5`
Note the `match_end` summary values: `red`, `blue`, `closed`, `tokens`, `llm_calls`, `red_llm_calls`, `blue_llm_calls`, `sweep_requests`, `cache_hits`.

- [ ] **Step 5: Update the sample-derived assertions**

In `tests/test_site_api.py`:

```python
    assert b["simulation_mode"] == "llm"
    assert b["llm_calls"] > 0 and b["tokens_used"] > 0
    assert b["red_llm_calls"] > 0 and b["blue_llm_calls"] > 0
    assert b["red_tokens"] > 0 and b["blue_tokens"] > 0
    assert b["sweep_requests"] == 0 and b["sweep_findings"] == 0
    assert b["cache_hits"] == 0
```

In `test_vulnerabilities_show_the_real_packet_and_diff`, the LLM may use different payloads:

```python
    assert sqli["affected_endpoint"] == "GET /api/search"
    assert "FLAG{sqli_leaked_db}" in sqli["detection_evidence"]
    assert sqli["mitigation"] and sqli["mitigation"] != sqli["root_cause"]
```
and for mass assignment:

```python
    assert "role" in mass["detection_evidence"].lower()
```

In `tests/test_server.py`:

```python
    assert events[0]["strategy"] == "llm"
```

Keep `types.count("breach") == 7` and `types.count("patched") == 7` (the sample must be 7/7); add `assert types.count("blue_diagnosis") == 7`.

- [ ] **Step 6: Run the sample-dependent tests**

Run: `.venv\Scripts\python -m pytest tests/test_site_api.py tests/test_server.py -q`
Expected: all pass. If a relaxed assertion still fails, inspect the sample event for that class and adjust the assertion to the real field (never the sample data).

Checkpoint: no commit.

---

### Task 8: Docs, full suite, browser verification

**Files:**
- Modify: `vibe-arena/README.md` (token strategy + run commands + sample line + status)
- Modify: `vibe-arena/docs/TEAM_TASKS.md` (call counts, `--demo`)
- Modify: `vibe-arena/docs/presentation/outline.md` if it states the old sample numbers

- [ ] **Step 1: Update the README**

Replace the token-strategy story with:

- Default match: `strategy: llm`; Red discovers with the model; Blue runs a diagnosis call then a patch call; no sweep, no cache.
- `--demo`: the deterministic sweep + verified-patch cache path (0 tokens) for offline judging.
- Templates: `get_payload_templates` is a hint tool Red may call; `RECIPES` guide Blue's patch step.
- Sample line: quote the new sample's calls/tokens/findings from Task 7 Step 4.
- Run command: `python -m pytest tests -q` with the new measured count.

- [ ] **Step 2: Update TEAM_TASKS**

Add: default LLM flow, `--demo` fast path, Blue two-phase diagnosis, new `blue_diagnosis` event.

- [ ] **Step 3: Run the full suite**

Run: `.venv\Scripts\python -m pytest tests -q`
Expected: all tests pass. Record the exact count and runtime; update README/TEAM_TASKS to that number.

- [ ] **Step 4: Browser verification**

Start `.venv\Scripts\python -m arena.cli serve` and `cd ui && npm run dev`.
In the Live Arena page:
- the sample shows Tier 1 "Not used in this match (LLM-only)", Tier 2 "LLM discovery + diagnosis + patch", non-zero RED and BLUE calls/tokens;
- Replay streams `Diagnosis:` events and the Blue panel shows `LOCATED: app/routes/...:fn:lines`;
- the final stream reads `Score - Red: 7 | Blue: 7` and `closed 7/7`;
- vulnerability popups flip to `DEFENDED`.

- [ ] **Step 5: Demo path check**

Run: `.venv\Scripts\python -m arena.cli run --demo --rounds 1`
Expected: sweep runs, cache replays verified fixes, `0 LLM calls · 0 tokens` when the cache is warm. Document the match id as the offline evidence.

Checkpoint: no commit; report results to Sidaarth.
