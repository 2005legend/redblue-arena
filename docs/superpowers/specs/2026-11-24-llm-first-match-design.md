# LLM-first match design

Date: 2026-11-24
Status: approved by Sidaarth; implementation target before Round 1 closes (2026-11-25)

## Problem

The default `hybrid` match runs the deterministic sweep first and lets the verified-patch cache
answer Blue. A normal demo therefore shows `0 LLM calls · 0 tokens` and looks like a scripted
attack. It is honest (the Tier 1 fast path is real), but it does not demonstrate the product:
models doing discovery and defence.

Red must find vulnerabilities by reasoning over the API, and Blue must locate the exploited code
point before patching. Scripts remain, but only as helpers: payload hints Red may request, Blue
patch recipes, and the `--demo` fast path.

## Decisions

1. Default strategy is `llm`. The deterministic sweep and the verified-patch cache run only with
   `--demo` (new flag) or an explicit `--strategy hybrid|sweep`.
2. Blue uses two model calls per finding: diagnosis, then patch. Diagnosis is logged and rendered.
3. Payload templates are an optional tool Red calls; they are never the default attacker.
4. The linked GitHub repo (`2005legend/redblue-arena`) is a reference only. The second website is
   expected the evening of 2026-11-24 and is out of scope here.

## Default flow

`python -m arena.cli run` (no flag):
- no `Sweep`, no cache lookup, `reuse_cache = False`
- Red runs in two rounds of up to 30 tool steps each
- Blue diagnoses then patches every finding
- events flush per emit; exports refresh after every verified patch

`python -m arena.cli run --demo`:
- sweep runs first, cache enabled, `should_run_llm("hybrid", ...)` gate applies
- identical to today's behaviour, so the offline zero-key story stays intact

`arena.yaml` ships `strategy: llm`; `--strategy` still accepts `hybrid`, `sweep`, `llm`.

## Red agent (`arena/red.py`)

- Replace the four-class `SYSTEM` with a seven-class playbook: enumerate routes, log in, then test
  SQLi, IDOR, admin bypass, path traversal, mass assignment, debug exposure and code injection
  systematically. Name already-breached routes and tell Red to move on.
- `get_payload_templates` description covers all seven classes (payloads already exist).
- Extend `classify()`:
  - path contains `admin` -> `admin_bypass`
  - `..` in path/params -> `path_traversal`
  - `'`, `--`, `OR`, `UNION` in path/params -> `sqli`
  - PUT/PATCH with `role` / `is_admin` / `admin` in the JSON body -> `mass_assignment`
  - `debug` / `diagnostic` in the path -> `debug_exposure`
  - path/params contain `expr` / `expression` / `eval` / `code` / `cmd` -> `code_injection`
  - numeric path segment -> `idor`
  - otherwise `unknown`
- Emit `"source": "llm"` on breach events.
- Context window cap: keep `SYSTEM`, the initial user intro (accounts + login state), a compact
  `findings_so_far` line, and only the last 6 tool turns. HTTP bodies stay truncated at 800 chars.
  The compact findings line lists `vuln_class route` pairs so Red does not repeat finished classes.

## Blue agent (`arena/blue.py`)

Phase 1, diagnosis (one model call):
- Input: exploit packet, narrowed candidate files, Blue recipes (class-specific hints)
- Expected reply format:
  `FILE: <path>` / `FUNCTION: <name>` / `LINES: <a-b>` / `ROOT CAUSE: <one or two sentences>` /
  `REACHED BY: <method path + payload>`
- Parse tolerantly. Log `blue_diagnosis` with `{file, function, lines, root_cause, reached_by}`;
  unparseable fields are logged as raw text in `root_cause` and the file is left unknown.
- If the call errors, log `blue_error`, skip diagnosis, and patch in single-phase mode.

Phase 2, patch (one or more attempts):
- Message contains the diagnosis plus the source of only the diagnosed file when it resolves to a
  real file inside `app/`; otherwise fall back to the narrowed file list. This is the token saving:
  Call 2 never resends the full candidate set when the diagnosis is usable.
- Existing SEARCH/REPLACE parsing, staging, referee verification and failure feedback are
  unchanged. `max_attempts` stays 3.
- Cache is consulted only when `reuse_cache` is true; on a hit, both phases are skipped.

## Orchestrator (`arena/orchestrator.py`)

- Parameters gain `reuse_cache: bool | None`; default from strategy (`llm` -> False).
- Build the sweep only when strategy is `hybrid`/`sweep`.
- After each verified patch, call `export(out_dir, exploits_closed, patches, ttps)` so a late
  provider failure never loses earlier deliverables; keep the final export in `match_end`.
- Summary keeps sweep fields; in LLM-only mode they are zero.

## Events and UI

New event `blue_diagnosis`:
```json
{"type": "blue_diagnosis", "vuln_class": "idor", "route": "/api/invoices/{id}",
 "file": "app/routes/invoices.py", "function": "get_invoice", "lines": "14-17",
 "root_cause": "..."}
```
- `ui/src/pages/BattleArenaPage.tsx`: render the event in the stream with a `[DIAGNOSIS]` tag and a
  `LOCATED: file:function:lines` line; show the latest diagnosis in the Blue panel.
- Tier panel: when no sweep ran, show `Tier 1 · deterministic -- not used (LLM-only)` and
  `Tier 2 · LLM agents -- discovery + diagnosis + patch` with per-side calls/tokens.
- `arena/site_api.py`: tolerate the new event in summaries; expose diagnosis fields alongside
  patches where they are available.

## Sample recording (point 3)

- Re-record `matches/` sample from a real LLM-only run through the FreeLLM router, with a token
  budget that allows a full 7/7 pass. If a provider failure interrupts the run, keep the partial
  run as evidence and retry; the bundled sample must show real Red and Blue call counts.
- `replay` remains the default zero-API-key path for judges.
- Incremental export (above) protects the run: findings 1..n-1 survive a failure on n.

## Testing

- `classify()` returns the right class for all seven request shapes.
- Diagnosis parser: well-formed reply, missing fields, malformed reply, and provider error.
- `run_blue` with a scripted fake LLM: first reply diagnosis, second reply edits; asserts the
  patch prompt contains only the diagnosed file; asserts `blue_diagnosis` is emitted before
  `blue_attempt`.
- Diagnosis failure falls back to single-phase patching and still verifies a good patch.
- Orchestrator default mode: `Sweep` is never constructed, Red runs, Red/Blue call counts are
  recorded, cache is untouched.
- Orchestrator `--demo` mode: sweep + cache still closes all seven with zero calls.
- Existing 91 tests stay green; suite count updated in README and TEAM_TASKS.

## Non-goals

- No UI replacement from the linked repo and no new target app tonight.
- No change to the referee, sandbox, host-lock, or patch-verification rules.
- No removal of `hybrid`/`sweep`; they are the offline demo path.

## Acceptance

- A default run shows non-zero Red and Blue LLM calls and a `blue_diagnosis` per finding.
- A `--demo` run still closes 7/7 from the cache with zero calls.
- Sample replay in the SOC UI shows both sides working and the diagnosis stream.
- Full test suite green.
