# Team tasks

Everyone commits from their own GitHub account (repo Settings -> Collaborators), on a branch, via a pull request.
Do not commit for someone else.

## Already done by the core team
Sandbox, referee, Red/Blue agents, test capture, exporter, match runner, replay server, arena UI, 4 bug classes
(SQLi, IDOR, admin bypass, path traversal) on fixtures/dev_target, 32 tests, sample match.

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
- Screenshots of the arena in docs/img/, used in the README and slides.
