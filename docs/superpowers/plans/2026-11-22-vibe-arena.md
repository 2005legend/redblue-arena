# Vibe Arena Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python tool that runs a Red (attacker) and a Blue (patcher) LLM agent against a sandboxed FastAPI app, with a deterministic referee, live
event stream, replay mode, export, and a React arena UI.

**Architecture:**
- The orchestrator starts the target app as `uvicorn` subprocesses on dynamic ports, each with a fresh copy of `seed.db`.
- Red attacks through a host-locked HTTP tool.
- Blue returns SEARCH/REPLACE edits. These are applied to a staging copy and verified with frozen functional tests plus the exploit replay, then
  swapped in by repointing `target_url`.
- Every event goes to a JSONL match log, which a FastAPI WebSocket server streams live or replays.

**Tech Stack:** Python 3.11, FastAPI, uvicorn, httpx, psutil, PyYAML, openai (OpenAI-compatible client), pytest; React + Vite (Node 24).

**Spec:** `docs/superpowers/specs/2026-11-22-vibe-arena-design.md`

## Global Constraints

- Red's HTTP tool refuses any host other than `127.0.0.1`/`localhost`, and any port not registered by the sandbox. Enforced in code.
- Blue never edits the live app dir or the frozen tests; it edits only the staging copy's `app/` files.
- Blue's output format is SEARCH/REPLACE blocks; the `.patch` comes from `difflib.unified_diff()`.
- Every target process gets its own copy of the immutable `seed.db`; no two processes share a DB file.
- No port is reused. Ports come from a counter starting at 8001. Old processes are killed as a whole tree with `psutil`.
- The LLM is configured only by env: `ARENA_BASE_URL`, `ARENA_API_KEY`, `ARENA_MODEL`, with optional `ARENA_RED_MODEL` and `ARENA_BLUE_MODEL`.
- Blue gets at most 3 attempts per breach.
- Referee: Red scores on a `FLAG{...}` in a response body. Blue scores only if 100% of frozen tests pass AND the replay no longer returns the flag.
- `fixtures/dev_target` is hand-written by us for development only and must be labelled so in its README. The demo target comes from Light 1 (spec 5.1).
- Must run on Windows.

## Review Focus

1. Blue's SEARCH text doesn't match the file exactly (whitespace/CRLF) → the attempt fails cleanly with a message fed back to Blue, with no crash.
   *Test in Task 5.*
2. A staging app fails to boot (syntax error in the patch) → `start()` times out, the process tree is killed, and the attempt is recorded as failed.
   *Test in Task 2.*
3. Blue "fixes" by making the route return 403 for everyone → the frozen functional tests fail and the patch is rejected. *Test in Task 5.*
4. The LLM returns no tool call, or malformed JSON arguments → the Red loop logs the error and continues, up to its step budget. *Test in Task 4.*
5. A Red request targets an external host (e.g. `http://example.com`) → `HostLockError` is raised, the request is never sent, and the attempt is logged.
   *Test in Task 3.*

---

## File Structure

```
vibe-arena/
  README.md
  requirements.txt
  arena.yaml                    # config for the current target
  fixtures/dev_target/          # hand-written dev target (NOT the demo app)
    README.md
    app/main.py  app/db.py  app/routes/{auth,invoices,admin}.py
    seed.py                     # builds seed.db
    tests_functional/test_happy.py
  arena/
    config.py      # load arena.yaml -> ArenaConfig
    sandbox.py     # TargetProcess: copy dir + seed.db, start uvicorn on port, kill tree
    httptool.py    # host-locked request sender
    payloads.py    # payload templates per vuln class
    referee.py     # find_flags, run_functional_tests, verify_patch
    llm.py         # OpenAI-compatible chat wrapper + token counting
    red.py         # Red agent loop
    blue.py        # SEARCH/REPLACE parse/apply, make_patch, blue loop
    capture.py     # functional test capture
    exporter.py    # security tests + report.md + hardened.patch
    events.py      # EventLog (jsonl + async subscribers)
    orchestrator.py# match rounds
    server.py      # FastAPI: /ws live, /replay, /export
    cli.py         # `python -m arena.cli run|replay`
  tests/           # pytest for arena/
  ui/              # Vite React app
  matches/         # recorded match logs (sample.jsonl bundled)
```

---

### Task 1: Dev target app + seed DB + functional tests

**Files:** create `vibe-arena/fixtures/dev_target/**`, `vibe-arena/requirements.txt`, `vibe-arena/arena.yaml`, `vibe-arena/README.md`

**Interfaces:**
- Produces: a FastAPI app `app.main:app`. It reads the DB path from env `ARENA_DB` (default `./seed.db`).
- Routes:
  - `POST /api/login {username,password}` → `{token}`. The token is `"tok-<user_id>"`; it's a dev fixture.
  - `GET /api/search?q=` builds raw SQL with an f-string. **SQLi**: `' OR 1=1--` leaks the hidden `FLAG{sqli_leaked_db}` row.
  - `GET /api/invoices/{id}` with no owner check. **IDOR**: invoice 3 belongs to bob and contains `FLAG{idor_invoice_leak}`.
  - `GET /api/invoices` → only the caller's own invoices.
  - `GET /api/admin/export` with no role check. **Admin bypass**: the body has `FLAG{admin_export_bypass}`.
- Users:
  - `alice / alice123` (user, id 1, invoices 1, 2)
  - `bob / bob123` (user, id 2, invoice 3)
  - `admin / admin123` (admin, id 3)
- `arena.yaml` keys:
  - `app_dir`, `app_module: app.main:app`, `seed_db: seed.db`, `functional_tests: tests_functional`;
  - `users: [{username,password,role}]`, `sample_ids: {own_invoice: 1, other_invoice: 3}`;
  - `admin_routes: [/api/admin/export]`.

- [ ] **Step 1:** Write `tests_functional/test_happy.py`. It reads the base URL from env `ARENA_TARGET`. Tests:
  - `test_login_ok`: 200 and has a token;
  - `test_search_normal`: `q=coffee` → 200 with ≥1 result;
  - `test_own_invoice`: alice gets invoice 1 → 200;
  - `test_list_own_invoices`: alice's list has ids {1, 2};
  - `test_admin_export_as_admin`: admin token → 200.
- [ ] **Step 2:** Implement the app and `seed.py`, then run `python seed.py` to create `seed.db`.
- [ ] **Step 3:** Start it with `uvicorn app.main:app --port 8000`, run `ARENA_TARGET=http://127.0.0.1:8000 pytest tests_functional`. Expected: 5 passed.
  Manually confirm that each of the 3 exploits returns its flag.
- [ ] **Step 4:** `git init` in `vibe-arena/` and commit.

### Task 2: Config + sandbox process manager

**Files:** `arena/config.py`, `arena/sandbox.py`, `tests/test_sandbox.py`

**Interfaces:**
- `load_config(path: str) -> ArenaConfig`. This is a dataclass with every `arena.yaml` key, where `app_dir` is resolved relative to the yaml.
- `class PortAllocator: next() -> int` (starts at 8001 and never repeats).
- `class TargetProcess(src_dir: Path, seed_db: Path, port: int, work_root: Path)`:
  - `.prepare() -> Path` copies `src_dir/app` and `seed_db` into `work_root/<port>/`;
  - `.start(timeout=15) -> None` launches `python -m uvicorn app.main:app --port N` with `ARENA_DB` set, polls `/openapi.json` until 200,
    and raises `TargetBootError` on timeout (after killing the tree);
  - `.stop()` kills the process tree with psutil;
  - `.url` and `.dir` properties.
- `ALLOWED_PORTS: set[int]` is a module-level registry. `start` adds the port and `stop` removes it.

- [ ] **Step 1:** Write the tests:
  - `test_start_and_stop`: the target boots, `GET /openapi.json` returns 200, and after `stop()` the port refuses connections;
  - `test_two_targets_isolated_db`: two targets on different ports; a write to one (sqlite directly on its copy) is not visible in the other;
  - `test_boot_failure_raises`: a src dir whose `main.py` has a syntax error raises `TargetBootError`, and no python child is left listening;
  - `test_ports_never_repeat`.
- [ ] **Step 2:** Run the tests. Expected: they fail (not implemented).
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run the tests. Expected: they pass. Commit.

### Task 3: Host-locked HTTP tool, payload templates, referee flag check

**Files:** `arena/httptool.py`, `arena/payloads.py`, `arena/referee.py` (first part), `tests/test_httptool.py`, `tests/test_referee.py`

**Interfaces:**
- `send_request(method: str, url: str, headers: dict|None=None, params: dict|None=None, json: dict|None=None) -> HttpResult`:
  - `HttpResult` is a dataclass with `status`, `headers`, `body: str` (truncated to 4000 chars), `elapsed_ms`;
  - raises `HostLockError` if the host isn't 127.0.0.1/localhost or the port isn't in `sandbox.ALLOWED_PORTS`.
- `PAYLOADS: dict[str, list[str]]` with keys `sqli`, `idor`, `admin_bypass`, `path_traversal`; `get_payload_templates(vuln_class) -> list[str]`.
- `find_flags(text: str) -> list[str]` uses the regex `FLAG\{[A-Za-z0-9_]+\}`.
- `@dataclass Exploit(method, path, headers, params, json, flag, vuln_class)`.
- `replay(exploit: Exploit, base_url: str) -> HttpResult`.

- [ ] **Step 1:** Write the tests:
  - `test_blocks_external_host` (example.com raises `HostLockError`);
  - `test_blocks_unregistered_port`;
  - `test_find_flags` (two flags in text → both found; no flag → `[]`);
  - `test_replay_returns_flag_on_dev_target` (start a TargetProcess, replay the IDOR exploit, the flag is found).
- [ ] **Step 2:** Run the tests. Expected: they fail.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run the tests. Expected: they pass. Commit.

### Task 4: LLM client + Red agent

**Files:** `arena/llm.py`, `arena/red.py`, `tests/test_red.py`

**Interfaces:**
- `class LLM(role: str)`:
  - reads env (`ARENA_RED_MODEL`/`ARENA_BLUE_MODEL` fall back to `ARENA_MODEL`);
  - `.chat(messages, tools=None) -> dict` returns the assistant message as a dict with `content` and `tool_calls`;
  - `.tokens_used: int`.
- `class FakeLLM` (in tests) returns scripted responses.
- `run_red(llm, base_url: str, openapi: dict, users: list[dict], emit: Callable[[dict], None], max_steps=25) -> list[Exploit]`:
  - tools exposed to the model: `discover_routes`, `send_http_request`, `get_payload_templates`;
  - after each `send_http_request`, `find_flags` runs on the body. A new flag becomes an `Exploit`, and `emit({"type":"breach",...})` is called;
  - every tool call emits `{"type":"red_action", "tool", "args", "status"}`.

- [ ] **Step 1:** Write the tests:
  - `test_red_records_breach`: FakeLLM scripts a login call, then the IDOR request → 1 Exploit with `flag=="FLAG{idor_invoice_leak}"`;
  - `test_red_survives_bad_tool_args`: FakeLLM returns invalid JSON args, then a valid call → no exception, and an error event is emitted;
  - `test_red_stops_at_max_steps`.
- [ ] **Step 2:** Run the tests. Expected: they fail.
- [ ] **Step 3:** Implement. The Red system prompt says:
  - it is attacking a local, consenting test app;
  - goal: find `FLAG{...}` strings;
  - try SQLi, IDOR and admin bypass using the templates.
- [ ] **Step 4:** Run the tests. Expected: they pass. Commit.

### Task 5: Blue patch pipeline

**Files:** `arena/blue.py`, `arena/referee.py` (second part), `tests/test_blue.py`

**Interfaces:**
- `parse_edits(text: str) -> list[Edit]`:
  - `Edit(path, search, replace)`;
  - format: `FILE: app/routes/x.py\n<<<<<<< SEARCH\n...\n=======\n...\n>>>>>>> REPLACE`.
- `apply_edits(app_dir: Path, edits) -> None`:
  - normalises CRLF/LF before matching;
  - raises `EditApplyError(path, reason)` if the search text isn't found exactly once.
- `make_patch(before_dir: Path, after_dir: Path) -> str` uses `difflib.unified_diff` over the changed files, with `a/` and `b/` prefixes.
- `run_functional_tests(tests_dir: Path, base_url: str) -> TestResult(passed: int, failed: int, output: str)`:
  - a pytest subprocess with `ARENA_TARGET` set.
- `verify_patch(staging: TargetProcess, exploit, tests_dir) -> Verdict(ok: bool, tests: TestResult, replay_flag_found: bool)`.
- `run_blue(llm, live_dir, exploit, logs: str, tests_dir, ports, work_root, emit, max_attempts=3) -> BlueResult(ok, patch: str, new_target: TargetProcess|None, attempts)`.

- [ ] **Step 1:** Write the tests:
  - `test_parse_and_apply_edit`;
  - `test_apply_crlf_tolerant`;
  - `test_apply_missing_search_raises`;
  - `test_make_patch_has_headers` (`--- a/app/routes/invoices.py`, `+++ b/...`);
  - `test_verify_accepts_real_fix`: a hand-written IDOR fix (owner check) → `ok=True`;
  - `test_verify_rejects_403_everyone`: a patch where `get_invoice` always raises 403 → `ok=False` because `test_own_invoice` fails;
  - `test_blue_retries_then_gives_up`: FakeLLM gives 3 non-matching edits → `ok=False`, `attempts==3`, and staging processes are stopped.
- [ ] **Step 2:** Run the tests. Expected: they fail.
- [ ] **Step 3:** Implement. Blue's prompt includes:
  - the exploit request and response;
  - recent log lines;
  - the full text of the route files (≤80 lines each);
  - the rule: "fix the root cause, keep normal behaviour, output only SEARCH/REPLACE blocks".

  Failure output (apply error or test output) is fed into the next attempt.
- [ ] **Step 4:** Run the tests. Expected: they pass. Commit.

### Task 6: Test capture + exporter

**Files:** `arena/capture.py`, `arena/exporter.py`, `tests/test_capture.py`, `tests/test_exporter.py`

**Interfaces:**
- `capture_tests(llm, openapi: dict, cfg: ArenaConfig, base_url: str, out_dir: Path) -> CaptureResult(kept: list[str], dropped: list[str])`:
  - the prompt gets the OpenAPI spec plus `users` and `sample_ids`;
  - drops tests that call `admin_routes` with a non-admin, or use `other_invoice`;
  - runs each test file; keeps the passing ones;
  - writes `out_dir/FROZEN.sha256`.
- `review_tests(out_dir) -> None`: a CLI prompt that lists the kept tests and asks y/n per file (skipped when `--yes` is passed).
- `export(match_dir: Path, exploits, patches: list[str], verdicts) -> Path`. It writes:
  - `hardened.patch`;
  - `tests/security/test_security_<slug>.py`: each asserts the replay response has no flag;
  - `report.md`.
- `security_test_source(exploit) -> str`.

- [ ] **Step 1:** Write the tests:
  - `test_capture_filters_cross_user` (FakeLLM emits one test fetching `other_invoice` → it is dropped);
  - `test_security_test_source_runs` (the generated file fails against the vulnerable dev target and passes after the real fix);
  - `test_export_writes_files`.
- [ ] **Step 2:** Run the tests. Expected: they fail.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run the tests. Expected: they pass. Commit.

### Task 7: Events, orchestrator, CLI, server, replay

**Files:** `arena/events.py`, `arena/orchestrator.py`, `arena/cli.py`, `arena/server.py`, `matches/sample.jsonl`, `tests/test_orchestrator.py`

**Interfaces:**
- `class EventLog(path: Path)`:
  - `.emit(event: dict)` adds `ts` and `seq`, appends a JSON line, and pushes to `asyncio.Queue` subscribers;
  - `.subscribe() -> asyncio.Queue`.
- Event types: `match_start{routes}`, `capture_done{kept,dropped}`, `red_action`, `breach{route,vuln_class,flag}`, `blue_thinking{text}`,
  `blue_attempt{n,ok,reason}`, `patched{route,patch,ttp_seconds}`, `score{red,blue}`, `health{passed,failed}`, `match_end{summary}`.
- `run_match(cfg, llm_red, llm_blue, log: EventLog, rounds=3, round_seconds=120) -> MatchSummary(red, blue, closed, total, tokens, ttp)`.
- CLI commands:
  - `python -m arena.cli run --config arena.yaml [--yes]`;
  - `python -m arena.cli replay matches/sample.jsonl`;
  - `python -m arena.cli serve`.
- Server:
  - `GET /ws` (WebSocket; live events or replay at 1×/4× speed via the `?replay=<file>&speed=` query);
  - `POST /api/match/start`;
  - `GET /api/export/{match_id}/{file}`.

- [ ] **Step 1:** Write `test_run_match_with_fakes`. FakeLLM Red finds the IDOR, then FakeLLM Blue returns the correct fix. Checks:
  - the summary has `closed==1`;
  - the log contains `breach` then `patched`;
  - the final `target_url` port differs from the first.
- [ ] **Step 2:** Run the test. Expected: it fails.
- [ ] **Step 3:** Implement. Hand-write `matches/sample.jsonl`: a full 3-breach, 3-patch match for UI development.
- [ ] **Step 4:** Run the test. Expected: it passes. Then run `python -m arena.cli replay matches/sample.jsonl` and expect the events printed in order. Commit.

### Task 8: Arena UI

**Files:** `ui/` (Vite React): `src/App.jsx`, `src/components/{Scoreboard,EndpointGrid,RedFeed,BlueFeed,EndScreen}.jsx`, `src/useArena.js`

**Interfaces:**
- Consumes: the `/ws` event stream from Task 7.
- `useArena(url) -> {score, endpoints: {route: "healthy"|"breached"|"patched"}, redEvents, blueEvents, health, summary}`.

- [ ] **Step 1:** `npm create vite@latest ui -- --template react`, then `npm i` and `npm i react-syntax-highlighter`.
- [ ] **Step 2:** Implement the components:
  - dark esports styling;
  - Red feed on the left, Blue feed on the right;
  - the diff rendered with a `diff` language highlighter;
  - the end screen shows closed X/Y, tests passing, time to patch per bug, tokens, and three download buttons.
- [ ] **Step 3:** Run `python -m arena.cli serve` and `npm run dev`, open `/?replay=sample.jsonl`. Expected: the endpoint grid goes
  healthy → breached → patched for all 3 routes, and the end screen appears.
- [ ] **Step 4:** Commit.

### Task 9 (today, if time): live pilot

- [ ] Set `ARENA_*` env to the free API and run `python -m arena.cli run --config arena.yaml --yes` against the dev target.
- [ ] Record Red's success per class over 3 runs, Blue's success, tokens per match, and any refusals.
- [ ] Write the results into the README "Pilot results" section.
