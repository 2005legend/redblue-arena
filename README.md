# Vibe Arena — Red vs Blue agents for AI-built apps

Compute 50 hackathon, Round 1, Domain 9 (Developer Productivity and Intelligent Automation).

You vibe-coded an app. Before you deploy it, **Red** (an attacker agent) tries to break it and
**Blue** (a defender agent) patches the source. A deterministic **referee** (no LLM) decides who
scored: Blue only scores if every frozen functional test still passes AND Red's exact exploit
is blocked. You get a hardened `.patch`, a report, and a security test per exploit.

Prior work we build on and cite: RvB (arXiv 2601.19726), OpenAI Daybreak, DARPA AIxCC, CAI (arXiv 2510.17521).
Our angle: aimed at people who ship AI-built apps with no security team and no tests.

Design: `docs/superpowers/specs/2026-11-22-vibe-arena-design.md`
Plan: `docs/superpowers/plans/2026-11-22-vibe-arena.md`

## Run it

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest tests -q            # 28 tests, about 45 s
.venv\Scripts\python -m arena.cli replay matches/sample.jsonl   # print a recorded match
```

Arena UI (replay needs no API key):

```powershell
.venv\Scripts\python -m arena.cli serve      # terminal 1, port 8765
cd ui; npm install; npm run dev              # terminal 2, open http://127.0.0.1:5173
```

Live match (needs an OpenAI-compatible LLM). Copy `.env.example` to `.env`, fill in
`ARENA_BASE_URL`, `ARENA_API_KEY`, `ARENA_MODEL` (the file is git-ignored and loaded automatically), then:

```powershell
.venv\Scripts\python -m arena.cli run --config arena.yaml --yes
```

Pointing it at another FastAPI app: copy `arena.yaml` and edit `app_dir`, `seed_db`, `functional_tests`,
two normal-user logins, `sample_ids`, `admin_routes`. `--capture` drafts the functional tests with the LLM
(you approve them unless `--yes`).

## Status (Nov 22)

Done and tested (28 tests): dev target with 3 seeded bugs, sandbox (per-port process + DB copy, psutil
tree kill), host-locked HTTP tool, referee, Red agent, Blue SEARCH/REPLACE pipeline with staging
verification, test capture + freeze, exporter, orchestrator, event log, WebSocket server with replay,
React arena UI.

NOT done yet:
1. **Live pilot (plan Task 9).** Never run against a real LLM. Measure per provider: valid tool calls,
   refusals on SQLi/IDOR payloads, Red success per class over 3 runs (pass bar 2 of 3), tokens per match.
   Write results below under "Pilot results". Use a free API first, buy DeepSeek only if it fails.
2. **Demo target app.** `fixtures/dev_target` is hand-written for development. The demo app must be
   generated with a real AI tool (Cursor, Copilot, ...) and described honestly: "unedited" only if the bugs
   appeared on their own, otherwise "representative of common AI-generated bugs".
3. `matches/sample.jsonl` is a hand-authored sample for UI work (diffs are real, events are not a live
   run). Replace it with a real recorded match after the pilot, and label recorded runs as recorded.
4. Path traversal class (stretch), demo video, PPT, prior-work slide.
5. Rules check: ask the organisers whether code written before Nov 23 is allowed.

## Pilot results

(empty)
