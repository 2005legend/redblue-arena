# Demo video script (about 3 minutes)

Shot-by-shot timing, the two-recording-pass plan, filming setup and fallbacks are in
`docs/demo/storyboard.md`; this file is the narration outline.

Record the arena UI at http://127.0.0.1:5173 (screen and voice), with the victim view open either in
its centre column or full screen at http://127.0.0.1:8765/target. Use the live match if the pilot
works; otherwise use the replay and say clearly on screen that it is a recorded run.

1. **0:00 Hook (15 s).** "Millions of people now build apps with AI and deploy them the same night. Nobody
   tests whether strangers can read other users data. We built Vibe Arena: two AI agents fight over your app
   before you ship it."
2. **0:15 Problem and prior work (25 s).** Show the prior-work slide. "Research like RvB and products like
   OpenAI Daybreak do this for security teams. Vibe Arena is for the solo builder with no tests and no
   security team."
3. **0:40 The arena, and the app it is attacking (55 s).** Start the match. Point at the centre column:
   "this is not a mock-up, this is the real storefront the agents are hitting, served from the sandbox
   port." Red logs in as a normal user and probes routes; the site's own response panel fills with the
   answer. A tile turns red, "Breached"; the victim page flashes and the storefront scrolls to the leak,
   with the canary highlighted. Blue reads the evidence and writes a fix.
4. **1:35 The site now refuses it (30 s).** After the verdict on that bug the victim page reloads the
   patched target and re-sends the same request: the storefront answers with no canary and the chip flips
   to "SQL INJECTION BLOCKED". Say: "same URL, same request, same site; the only thing that changed is
   the code." If there is time, click one **Manual probe** to show it live.
5. **2:05 Why you can trust the fix (30 s).** "A referee with no AI decides. Blue only scores if every
   normal-user test still passes AND the exact attack now fails. Deleting the route or blocking everyone
   fails the tests."
6. **2:35 What you get (20 s).** End screen: closed X of Y, tests passing, time to patch. Show the
   downloads: hardened.patch, the new security tests, the report.
7. **2:55 Close (10 s).** "It runs on a free API key, attacks only a local sandbox, and never touches
   production. Vibe Arena: attack it before they do."

## Before recording

```powershell
set ARENA_KEEP_TARGET=1        # keeps the patched target alive after the verdict so the site stays up
.venv\Scripts\python -m arena.cli serve
cd ui; npm run dev             # open http://127.0.0.1:5173 and click "Live Arena"
```

Open http://127.0.0.1:8765/target in a second window for the full-screen victim shot. A warm cache
(`patches/cache.json`) closes every bug in about two minutes; delete it only if you want to film Blue's
model writing a patch.

Honesty rules for the video: say "recorded run" for any replay; do not call the demo app "AI-built" (see
targets/shop_app/GENERATION_LOG.md); say it is "representative of common AI-generated bugs".
