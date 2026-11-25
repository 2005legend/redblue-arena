# Demo video storyboard (3:05)

Three claims the video has to land, in this order:

1. **The site is real.** A viewer must see an ordinary storefront leak another user's data — not a log line.
2. **The fix is verified, not claimed.** The same request must be refused afterwards, by the same site.
3. **The AI is doing the work.** The warm-cache run is 0 tokens on purpose; the video has to show the model
   writing a patch too, or judges will call it a script.

The trick is that claim 1 and 2 happen in a real match (about 2 minutes, predictable), and claim 3 is a second,
shorter recording inserted near the end. Record the two passes separately, edit them into one story.

---

## Pass A — the live match (backbone, ~2 min of footage)

Start the stack with keep-target on, warm cache present:

```powershell
cd vibe-arena
$env:ARENA_KEEP_TARGET=1
.venv\Scripts\python -m arena.cli serve          # terminal 1, port 8765
cd ui; npm run dev                               # terminal 2, port 5173
```

Open and pre-load, in this order: `http://localhost:5173` (Arena), `http://127.0.0.1:8765/target`
(full-screen victim), the Patches page, and `http://127.0.0.1:8765/target` again in a second tab
scrolled to the response panel. Leave them loaded; switching tabs is dead air.

Then click **Start Live Match** and record continuously. The match runs ~115 s: breaches land 6–35 s,
the first patch ~38 s, then one patch every ~7 s, verdict at the end. The final target stays up.

## Pass B — the model actually writes the patch (~40 s of footage)

```powershell
Remove-Item patches\cache.json
.venv\Scripts\python -m arena.cli run --config arena.yaml --yes
```

Blue must fetch a fresh patch for each class; the Tier 2 box in the UI flips to `cache miss, model ran`
with real calls and tokens. A fully cold 7-class run is about seven model calls: the measured cold
4-class run was 4 calls / 3,964 tokens, and the cold 7-class run before the recipe fix was 15 calls /
21,768 tokens (two classes failed and were fixed afterwards). Read the number off the screen rather than
promising one in the voiceover. If the provider is down tonight, play back
`matches/live-20261124-081222` in the UI (7/7 closed, 2 calls, 2,329 tokens) and label it on screen as a
recorded run.

---

## Shot list

| Time | Picture | Action | Voiceover |
|---|---|---|---|
| 0:00–0:06 | Three hard cuts, zoomed on the leaked row: `FLAG{idor_invoice_leak}` | none | "This invoice belongs to bob. Alice can read it. Nobody noticed." |
| 0:06–0:18 | Full-screen MiniShop storefront, clean | slow scroll of the page | "Millions of apps get built with AI and shipped the same night. Almost none are tested for this." |
| 0:18–0:30 | Arena: RED / TARGET / BLUE, Tier strip | none | "Vibe Arena. Red attacks your app, Blue patches it, and a referee with no AI decides who scored." |
| 0:30–0:38 | Click **Start Live Match**; panel flips to `LIVE :8001` | hover the victim panel | "One click: the app and a fresh database are copied into a throwaway localhost sandbox. These are the only hosts it will ever touch." |
| 0:38–1:05 | Split: Red feed left, victim page right | let SQLi land, then IDOR | "Red is a real attacker agent. SQL injection dumps the product table, it reads another user's invoice, and it calls the admin export with a normal account." |
| 1:05–1:25 | Victim page full screen, response panel centred | let it scroll itself to the output | "Notice what is leaking: the same storefront, not a mock. The canary is the app's own row — `bob.private_invoice FLAG{idor_invoice_leak}`." |
| 1:25–1:50 | Arena: Blue feed, a real diff | point at the changed lines | "Blue reads the handler and writes a fix. Nothing lands until the referee re-runs every frozen functional test and Red's exact attack on a staging copy." |
| 1:50–2:05 | Victim page after the port swap | replay fires by itself: `[]`, `BLOCKED`, chip flips | "Same URL, same request. The only thing that changed is the code." |
| 2:05–2:35 | Cut to Pass B: cold cache, `model ran`, diff, tokens | hold on the numbers | "That run used a verified cache: zero tokens. Delete it and the model has to write the patch itself — the calls and tokens are right there in the panel — and the referee still verifies the result." |
| 2:35–2:50 | End screen, then Downloads | click hardened.patch, security tests, report | "You get the hardened patch, one security test per exploit, and a report with the time to patch." |
| 2:50–3:05 | Static: vulnerable vs blocked split screen (`docs/img/victim-attack.png` / `victim-blocked.png`) | none | "The demo app is hand-written to represent common AI-generated bugs — we asked an AI for a shop app and it came out secure. It runs on a free key, attacks only localhost, never production. Attack it before they do." |

Caption every number on screen so a judge can read it with the sound off: `7/7 closed`, `9/9 tests`,
`6.6–9.1 s to patch`, `0 tokens (warm)`, `4 calls / 3,964 tokens (cold)`.

## 60-second cutdown (for a pitch or a submission portal)

| Time | Beat |
|---|---|
| 0:00–0:06 | The leak, zoomed, no narration |
| 0:06–0:16 | Arena + one sentence: attack, patch, referee |
| 0:16–0:35 | Live: SQLi breaches, the site shows the canary |
| 0:35–0:45 | Patch verified; same request answers `BLOCKED` |
| 0:45–0:55 | Cold-cache clip: "the model wrote this patch" + tokens |
| 0:55–1:00 | Artifacts + honesty line + tagline |

## Filming setup

- 1920×1080, 30 fps. Browser at 110–125 % zoom, bookmarks bar hidden, one window per capture.
- Capture the Arena window and a second cropped capture of the victim's **response panel** (browser zoom
  150 %, scrolled to the output). Switch to the cropped capture when the leak happens — it is readable at
  1080p where the whole page is not.
- Turn off notifications; quit Slack/Teams; hide the mouse unless you are pointing at something.
- Record voice separately against a silent screen pass if you can; it is easier to match 3:05 exactly.
- Dry run once with no mic to confirm the victim panel appears and the match finishes in time.

## If something fails on the night

| Failure | Fallback |
|---|---|
| No model provider (Tailscale host down) | Play `matches/live-20261124-081222` in the UI and say "recorded run" — the UI badges it. |
| Victim panel shows `OFFLINE` | `serve` was started without `ARENA_KEEP_TARGET=1` or from the wrong directory; restart from `vibe-arena/`. |
| Port already in use / kept target from a previous take | Stop the previous `python`, or start a fresh `serve` (a new match kills the kept one). |
| Match stalls mid-way | Skip ahead: the **Manual probe** row on the storefront replays any class in one click, on camera. |
| Dashboard cluttered with old takes | Cover it with a new match; old `matches/live-*` directories are git-ignored, delete them if the selector list looks messy. |

## Honesty lines that must stay in

- Replayed footage is labelled as a replay (the UI puts `RECORDED LOG REPLAY` / `SAMPLE REPLAY` on it; do not crop that out).
- The demo app is "representative of common AI-generated bugs", never "unedited AI output".
- The warm run really is 0 tokens — say why (sweep + verified cache), do not imply the model did that work.
