# Team tasks

Everyone commits from their own GitHub account (repo Settings -> Collaborators), on a branch, via a pull request.
Do not commit for someone else.

## Already done by the core team
Sandbox, referee, Red/Blue agents, test capture, exporter, match runner, replay server, SOC site + classic replay UI,
7 bug classes
(SQLi, IDOR, admin bypass, path traversal, mass assignment, debug endpoint exposure, eval code
injection) on fixtures/dev_target, 99 tests (all passing on Nov 25; one Windows temp-dir flake in
test_capture.py can show up in a one-process run), sample match.
Token strategy (Nov 23): deterministic template sweep finds all current bugs at 0 tokens in a normal run; Blue uses
per-class recipes, narrowed file lists and a verified-patch cache (patches/cache.json) so repeated matches need no
LLM calls. See "Token strategy: two tiers" in the README. New targets just need `strategy`, `login_path` and
`loot_paths` set in their arena.yaml.
Run modes today: the default match is still `hybrid`; `arena.llm.yaml` runs `strategy: llm` with no sweep
and its own cache (`patches/cache.llm.json`), so Red and Blue must use their models. The server also serves
a live victim view at `/target` (embedded in the Target App page and in the Arena centre column), and
`ARENA_KEEP_TARGET=1` (or `--keep-target`) keeps the patched target alive after the verdict for filming.

## Person A: demo target and pilot support
- Try 2-3 more AI tools or prompts for a shop app (targets/shop_app/GENERATION_LOG.md shows how, and that our
  first attempt came out secure). Keep any version where bugs appear on their own, in targets/NAME/, with its
  own arena.yaml and an honest log of tool, prompt and edits. Seed canary flags FLAG{...} by hand and say so.
- Once the API key is in .env, run: python -m arena.cli run --config targets/NAME/arena.yaml --yes
  and write what happened under "Pilot results" in the README.

## Person B: quality and setup
- Fresh-machine test (Windows, and Mac if possible) of the README steps; fix anything unclear.
- More payload templates in arena/payloads.py plus a test in tests/test_payloads.py.
- Write docs/TROUBLESHOOTING.md (port already in use, missing API key, uvicorn not found).

## Person C: presentation and video (non-technical)
- Build the deck from docs/presentation/outline.md (PowerPoint), save it in docs/presentation/.
- Record the demo using docs/demo/script.md. Do not commit the video file; put the link in the README.
- Record one **LLM-only** match so the video shows the AI, not only the sweep: delete
  patches/cache.llm.json, run `python -m arena.cli run --config arena.llm.yaml --yes`, then play it back
  next to the 0-token sample. The Arena page shows Tier 1 vs Tier 2 calls/tokens from the log.
- For footage of the victim, the Live Arena page already embeds the site in its centre column; open
  http://127.0.0.1:8765/target for the full-screen version while a match runs. Start `serve` with
  ARENA_KEEP_TARGET=1 to film the patched site after the verdict too. Each breach is replayed inside
  the real storefront and each accepted fix is replayed against the patched target, so the site itself
  shows the leak and then the refusal. The storefront's "Manual probe" row repeats the seven requests
  by hand if you need a shot without waiting for the agents.
- Screenshots of the arena in docs/img/, used in the README and slides.
