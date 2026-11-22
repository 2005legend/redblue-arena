# Demo video script (about 3 minutes)

Record the arena UI at http://127.0.0.1:5173 (screen and voice). Use the live match if the pilot works;
otherwise use the replay and say clearly on screen that it is a recorded run.

1. **0:00 Hook (15 s).** "Millions of people now build apps with AI and deploy them the same night. Nobody
   tests whether strangers can read other users data. We built Vibe Arena: two AI agents fight over your app
   before you ship it."
2. **0:15 Problem and prior work (25 s).** Show the prior-work slide. "Research like RvB and products like
   OpenAI Daybreak do this for security teams. Vibe Arena is for the solo builder with no tests and no
   security team."
3. **0:40 The arena (60 s).** Start the match. Red logs in as a normal user and probes routes; a tile turns red,
   "Breached"; Blue reads the evidence and writes a fix; the tile turns green, "Patched". Point at the diff.
4. **1:40 Why you can trust the fix (35 s).** "A referee with no AI decides. Blue only scores if every
   normal-user test still passes AND the exact attack now fails. Deleting the route or blocking everyone
   fails the tests."
5. **2:15 What you get (30 s).** End screen: closed X of Y, tests passing, time to patch. Show the downloads:
   hardened.patch, the new security tests, the report.
6. **2:45 Close (15 s).** "It runs on a free API key, attacks only a local sandbox, and never touches
   production. Vibe Arena: attack it before they do."

Honesty rules for the video: say "recorded run" for any replay; do not call the demo app "AI-built" (see
targets/shop_app/GENERATION_LOG.md); say it is "representative of common AI-generated bugs".
