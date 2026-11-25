# dev_target - development fixture (NOT the "AI-built" demo app)

Hand-written by the Vibe Arena team to develop and test the arena. It deliberately contains one
vulnerability per bug class the arena tests today, each with a canary flag:

| Class | Route |
|---|---|
| SQL injection | `GET /api/search?q=` |
| IDOR | `GET /api/invoices/{id}` |
| Missing admin role check | `GET /api/admin/export` |
| Path traversal | `GET /api/files?name=` |
| Mass assignment | `PUT /api/profile` |
| Debug endpoint exposure | `GET /api/debug/config` |
| Code injection (eval) | `GET /api/calc?expr=` |

It also serves a MiniShop storefront at `GET /` so the live victim view has a real UI to attack
while a match runs.

This app is **not unedited AI output** and must never be described as such. It is representative
of the mistakes AI-generated apps commonly ship with. We asked a fresh agent for a shop app with a
plain feature prompt and it came out secure (see `targets/shop_app/GENERATION_LOG.md`), which is
exactly why this fixture is hand-written and labelled.

Accounts: `alice / alice123`, `bob / bob123`, `admin / admin123`. Every canary is a `FLAG{...}`
string a route returns when it is abused; `arena.yaml` declares which account owns each one, so an
attacker reading their own data is not scored as a breach.
