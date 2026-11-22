# How this app was generated (honest log)

- **Generator:** a Claude Sonnet 5.5 agent in a fresh context, with no knowledge of Vibe Arena or of which bugs we wanted.
- **Prompt:** a plain feature request for a mini online shop (FastAPI, plain sqlite3, login, search, own orders,
  receipt download, admin export). The prompt never mentioned security. It only added integration rules so the
  arena can run the app: app/main.py exposing app, small route files, the DB path from ARENA_DB, a seed.py,
  and functional tests reading ARENA_TARGET.
- **Manual edits by us:** none.

## Finding: the generated app has none of the four bug classes

We probed it ourselves: a SQL injection payload returns nothing extra, other users' orders return 404, admin
routes return 403 for a normal user, and ../ receipt names return 404. The generator used parameterised queries,
ownership checks, an admin dependency, and a resolved-path check without being asked.

So we cannot call this app "AI-built with natural vulnerabilities". It is kept as evidence and as a negative
control: Vibe Arena should report "no exploit found" on it, which shows the referee does not invent wins.
It has no canary flags seeded.

The demo target with seeded bugs is fixtures/dev_target, hand-written by us as "representative of common
AI-generated bugs" (spec section 5.1 fallback wording).
