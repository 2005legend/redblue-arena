# Vibe Arena: Red vs Blue agents for AI-built apps — Design

Date: 2026-11-22
Event: Compute 50 Hackathon (PSG Tech), Round 1, Domain 9: Developer Productivity and Intelligent Automation
Working name: "Vibe Arena" (placeholder, rename freely)

## 1. Intent and why

Many people now build web apps with AI tools (Cursor, Lovable, Bolt, Copilot) and deploy them the same day. These apps often ship with
access-control and injection bugs: IDOR, missing role checks, SQL injection. Their builders don't know these bug classes exist.

Vibe Arena takes such an app before deploy, puts it in a sandbox, and runs two AI agents against it:

- **Red** attacks it and tries to capture canary flags.
- **Blue** reads the evidence and writes a source-code patch.

A deterministic referee accepts a patch only if:
- normal-user behaviour still works (frozen functional tests), and
- Red's exact exploit is now blocked (replay).

The user leaves with:
- a hardened `.patch`;
- a proof-of-fix report;
- a test suite they never had (functional tests plus one security test per exploit).

The team's goal is to reach the top 20 of 118 teams. Evaluation includes novelty. Deliverables are a working prototype, a demo video, a PPT
and a GitHub repo. Round 1 runs Nov 23–25, 2026, with results on Nov 30. The finals are on campus on Dec 4–5, with new problem statements.

## 2. Prior work and the novelty claim

We cite these honestly on a slide:
- the RvB paper (Shanghai AI Lab, Jan 2026, arXiv 2601.19726): Red/Blue loop with regression-tested patches;
- OpenAI Daybreak Red Team + Defense Factory (announced Nov 12, 2026): enterprise, waitlist;
- DARPA AIxCC (2025): autonomous find-and-patch on open-source C/Java projects;
- the CAI attack/defense CTF study (arXiv 2510.17521).

**We do NOT claim** "first AI that exploits and patches code".

**Our claim:**
1. **Aimed at the person who vibe-coded an app last night.** No security team, no existing tests, free/cheap models. It is not aimed at enterprise security teams.
2. **Works with zero existing tests.** The tool *captures* a functional test suite from the running app before the battle, so the anti-cheating
   gate works on apps that shipped without tests.
3. **Every exploit becomes a permanent regression test**, committed to the repo, so the bug cannot quietly come back.
4. A watchable live arena that makes security understandable to non-experts.

Do not put "CYBERGENESIS" or "RedAgents.ai" on slides: we could not verify that they exist.

## 3. Goals, non-goals, anti-goals

**Goals (Round 1)**
- One end-to-end match on a real AI-generated FastAPI app: Red breaches → Blue patches → referee verifies → replay blocked → export.
- At least 3 vulnerability classes working end to end: SQLi, IDOR, admin/role bypass. Path traversal is a stretch goal.
- Works on *any* FastAPI app with an OpenAPI spec (routes come from `/openapi.json`). The demo uses one app.
- Arena UI with scoreboard, endpoint status grid, Red feed, Blue feed with the diff, and an end screen with export.
- Demo video, PPT, and a public GitHub repo with a README.

**Non-goals**
- Express/Node targets. Mention them as future work only.
- Auto-deploying patches to production. The output is a diff for a human to review.
- Network/OS-level attacks, scanning third-party hosts, or real CVE hunting.
- User accounts, persistence, or a multi-app dashboard.

**Anti-goals (it fails even if it "works" when…)**
- Blue "wins" by deleting routes or returning 403 to everyone (the frozen functional tests must prevent this).
- The demo claims an "untouched AI-built app" but we planted the bugs by hand (see 5.1).
- Red can send traffic anywhere other than the sandbox.
- The demo depends on a lucky live run with no fallback.

## 4. Constraints

- **Time:** 3 days of build (Nov 23–25), including the video and PPT. The finals need a reliable demo.
- **Team:** 4 people (confirmed). Two "core" members do the heavy lifting; two "light" members, one of them non-technical, take the rest:
  - **Core A:** orchestrator, Red agent, Blue agent, LLM layer, patch copy/verify/swap pipeline.
  - **Core B:** referee, test capture, security-test export, match log and replay mode, WebSocket server, then the arena UI. UI work starts
    on day 1 against a hand-written sample match log.
  - **Light 1 (technical-ish):** generates 2–3 candidate vibe-coded target apps with an AI tool from a plain feature prompt (day 1, morning).
    Records which tool and which prompt were used, and which bugs appeared on their own. Later writes the README and setup steps and tests the setup on a clean machine.
  - **Light 2 (non-technical):** PPT, demo video script and recording/editing, prior-work slide, end-screen copy. Starts on day 1 from
    this doc.
- **App generator tool:** still unconfirmed. Whatever tool Light 1 actually uses is named truthfully in the demo (see 5.1).
- **LLM access:**
  - the user has a "free LLM API" set up via GitHub (exact service unconfirmed; see section 8);
  - DeepSeek API (paid, ~₹500–600 planned).
- **Safety:** all attack traffic stays on localhost and the sandbox port. Enforced in code.

## 5. Design

### 5.1 Target app ("the patient")
- A small fintech or e-commerce API: users, login, invoices/orders, file download, admin export. FastAPI with SQLite.
- **Honesty rule:** on day 1, generate 2–3 candidate apps with a real AI tool from a plain feature prompt, with no mention of security. Keep the one
  where the bugs appear on their own.
  - If every bug appears on its own, the demo may say "built with <tool>, unedited".
  - If any bug had to be added by hand, the wording must be "representative of common AI-generated bugs", and the README says which ones.
- Canary flags are seeded in the data, e.g. `FLAG{idor_invoice_leak}`, in another user's invoice, the admin export, or a hidden DB row.

### 5.2 Test capture (before the battle)
- Read `/openapi.json` **and `arena.yaml`** (the normal-user logins and sample record IDs, so the tests don't fail with 401/404). An LLM drafts happy-path `pytest` tests for normal users (log in, view *own* invoice, create an order, …).
- Run them against the unpatched app. Keep only the passing ones, then **freeze** them (hash recorded). Neither agent can edit them.
- These become part of the user's deliverable.

### 5.3 Red agent
- Tool-calling agent. Tools:
  - `discover_routes` (from the OpenAPI spec);
  - `send_http_request`;
  - `inspect_response`;
  - `get_payload_templates(vuln_class)`.
- **Deterministic floor:** the tools ship built-in payload templates for each vulnerability class (SQLi strings, ID enumeration, role-header/
  token tampering, `../` paths). The LLM picks and adapts them; it doesn't invent everything from scratch.
- **Host lock in code:** the HTTP tool refuses any host or port except the sandbox target. A prompt instruction alone doesn't count.
- Red stops after a step/token budget per round.

### 5.4 Blue agent
- Inputs:
  - access log;
  - error traces;
  - Red's winning request (exploit record);
  - the target's source files.
- Outputs **SEARCH/REPLACE blocks** (or the full patched file), never a raw unified diff, because LLMs get diff line counts wrong. Route
  files stay small (~40–80 lines). The orchestrator builds the `.patch` deterministically with `difflib.unified_diff()`.
- **Never patches the live server.** Pipeline:
  1. apply the edits to a staging copy of the app;
  2. copy the immutable `seed.db` snapshot into the staging folder, so verification never shares a DB file with the live app (avoids
     `database is locked` and Red's state mutations);
  3. start the copy on the next free dynamic port (8001, 8002, …);
  4. run the frozen tests and the exploit replay against the copy;
  5. if both pass, point the orchestrator's `target_url` at the new port and kill the old process tree with `psutil` in the background.
     No port is reused, which avoids `WinError 10048` on Windows;
  6. if not, kill the staging process tree and feed the failures back to Blue.
- Gives up after N attempts (default 3), and the route stays "breached".

### 5.5 Referee (deterministic, no LLM)
- **Red scores** when a response contains a canary flag, or when protected state changes (e.g. another user's record changes).
- **Blue scores** when its patch passes 100% of the frozen tests and the exploit replay no longer leaks the flag or changes state.
- Each winning exploit is turned into a `pytest` security test (`test_security_<route>_<class>.py`) and added to the deliverable.

### 5.6 Orchestrator
- Python process. Runs the match as rounds:
  1. capture tests;
  2. Red attacks;
  3. on a breach, Blue patches;
  4. verify;
  5. Red tries again, including bypass attempts on patched routes;
  6. stop on the time or round limit.
- Writes every event to a JSON-lines match log and streams it over WebSocket.
- **Replay mode:** the UI can play back a recorded match log without calling any LLM. This lets the UI be built without spending tokens, and
  gives a guaranteed fallback for the finals.

### 5.7 LLM layer
- One OpenAI-compatible client. `base_url`, `model` and key come from env. Red and Blue can use different providers or models.
- Token usage is counted per match and shown on the end screen.

### 5.8 Arena UI (React + WebSocket)
- **Top bar:** Red vs Blue score, round timer, app health (tests passing).
- **Centre:** endpoint grid with the states Healthy → Breached → Patched.
- **Left feed:** Red's recon and payloads. **Right feed:** Blue's analysis and a syntax-highlighted diff.
- **End screen:**
  - vulnerabilities closed (X/Y);
  - functional tests passing;
  - time to patch per bug;
  - tokens used;
  - buttons: Download `.patch`, Download security tests, Download report (Markdown).

### 5.9 Deliverable export
- `hardened.patch`, `tests/functional/`, `tests/security/`, and `report.md` (each vulnerability with its exploit request, the fix diff, and before/after replay results).

## 6. Approaches considered

- **Angle (chosen: vibe-coded apps).** Other options:
  - "every exploit becomes a permanent test" as the lead angle (kept as feature 3 instead);
  - generic enterprise Red/Blue, rejected because RvB and Daybreak already cover it.
- **Target generation (chosen: pre-generated, honestly labelled).** Generating the app live on camera was rejected because nothing guarantees the bugs appear.
- **Scope (chosen: 3 vulnerability classes first, 4th only if day 2 is on schedule).** All 4 plus the full UI was rejected as too risky for 3 days.

## 7. Day plan (proposal)

- **Day 1 (Nov 23):**
  - LLM pilot (see 8);
  - generate and choose the target app;
  - test capture;
  - Red breaches all 3 classes from the CLI;
  - referee detects flags.
  - **Checkpoint:** Red success rate per class, measured on 3 runs each.
- **Day 2 (Nov 24):**
  - Blue patch pipeline with the copy/verify/swap flow;
  - security-test export;
  - match log and replay mode;
  - UI against replay logs.
  - **Checkpoint:** one full live match end to end.
- **Day 3 (Nov 25):**
  - polish, and path traversal if on schedule;
  - record the demo video (several takes allowed);
  - PPT;
  - README with setup;
  - submit.

## 8. Decisions and open unknowns

**LLM provider (to decide after the day-1 pilot, about 30 min).**

For each provider, check:
- valid tool calls;
- whether it writes SQLi/IDOR payloads against localhost without refusing;
- tokens per match;
- rate limits.

Plan: use the free API for development if it passes, and buy DeepSeek only if the free API fails the pilot or hits rate limits during a match. Check DeepSeek's current
pricing page; we expect one match to be cheap, but tokens per match are unknown until measured.

**Unknown until day 1:**
- Red's first-try success rate per vulnerability class;
- model refusal rate;
- whether the chosen AI tool produces the bugs on its own.

## 8b. Calls made after the builder review (marked as Claude's call; change any)

- **"Any FastAPI app" scope.** The demo uses our own app, with flags and test accounts seeded by hand. Generality means:
  - a user can point the tool at another FastAPI app by writing a small `arena.yaml` (base URL, two normal-user logins, one admin-only
    route list, optional flag locations);
  - routes still come from `/openapi.json`;
  - automatic DB seeding is future work.

  Red starts with one low-privilege account, plus a second account for IDOR. Slide wording: "works on FastAPI apps with a 10-line config".
- **Judges may run the repo.** Plan for it cheaply:
  - one-command setup in the README;
  - `--replay` mode as the default for anyone without API keys (it plays a bundled recorded match);
  - tested on Windows.
- **Test capture gets a quick human review.** Tests are auto-drafted, then shown in the terminal or UI for a ~2-minute approve/reject before freezing.
  - Automatic filter: keep only tests where a user touches their *own* resources.
  - Drop any test that asserts success on admin routes for a non-admin.

  Slide wording: "auto-drafted, human-approved in 2 minutes", not "fully automatic".
- **Red pass bar and fallbacks.** At the day-1 checkpoint, a class passes if Red breaches it in at least 2 of 3 runs. If it fails:
  1. lean harder on payload templates (still a live run; wording stays "live");
  2. otherwise drop that class from the demo.

  Any match shown from a recorded log is labelled "recorded run" on screen. We never hand-script Red's choices.
- **SQLi naturalness.** ORM-based generated code rarely has SQLi. We allow a plain feature prompt that asks for raw `sqlite3` (a normal
  beginner request). If SQLi still doesn't appear on its own, the "representative" wording rule from 5.1 applies.
- **Pitch wording on tools.** Lovable and Bolt are named as part of the problem (who vibe-codes). The demo app's actual generator is named truthfully.
  JS/Supabase targets stay future work.

## 8c. Decision: build the core on Nov 22 (before Round 1 opens)

- **Reason:** the user's Claude subscription ends on Nov 22. The goal is to finish 50%+ of the heavy lifting today; later work happens with free-tier
  tools (OpenCode, Antigravity).
- **Risk:** the page says teams "build and submit a working prototype" during Nov 23–25. If the rules forbid code written before the window,
  building early could disqualify the team. The team checks the rules or asks the organisers. Commit history is never backdated or faked.
- **Consequence for the code:** the code must be easy for free-tier tools to continue. That means small files, a clear README of what's done and what's
  left, and plain Python with few dependencies.

## 8d. Finding after building: an AI-generated app came out secure (Nov 22)

We asked a fresh Claude Sonnet 5.5 agent for a mini shop app from a plain feature prompt (no security wording).
It used parameterised SQL, ownership checks, an admin dependency and a resolved-path check, so none of SQLi,
IDOR, admin bypass or path traversal appeared. Consequences, decided by the core team (change any):
- The pitch must NOT claim "AI apps always ship these bugs". Honest wording: AI tools often get these wrong,
  especially under quick prompts and weaker models; Vibe Arena verifies instead of trusting.
- The demo target is `fixtures/dev_target`, described as "representative of common AI-generated bugs" (5.1 rule).
- `targets/shop_app` is kept as a negative control: the arena should find nothing and not invent a win.
- Cost if wrong: a judge may say the premise is unproven. Mitigation: try weaker models or rushed prompts and
  report how often bugs appear; that is a measurable result for the slides.

## 9. Left to the builder

- Exact folder layout, library choices inside the stack, prompt wording, UI styling, WebSocket message schema, and the payload template contents.
- Whether the orchestrator runs the target with `uvicorn` subprocesses or Docker (subprocesses are recommended for speed).
