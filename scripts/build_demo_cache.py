"""Build patches/cache.demo.json for the demo_shop target WITHOUT a live LLM.

Do not misunderstand this file: it does NOT bypass the referee. For each seeded bug this script
defines a hand-written SEARCH/REPLACE fix, then runs it through the arena's real pipeline
(staging copy -> boot -> frozen functional tests -> exploit replay). Only fixes the referee
accepts are stored with arena.blue.store_edits(), keyed exactly like Blue's own output, so a
live demo match verifies every entry on staging again before it is accepted (arena/blue.py
cached_edits path). If an entry stops verifying, the orchestrator drops it and Blue's model
must write a new one - which is the honest cold-cache story for the video.

Provider note (Nov 25): the LLM host is unreachable, so patch writing cannot be shown live.
Delete patches/cache.demo.json once the provider is back to demo a cold run; the fixes in this
script are a fallback backstop, not a substitute for the model.
"""
import httpx

from arena.blue import Edit, _stage_and_verify, store_edits
from arena.config import load_config
from arena.referee import Exploit
from arena.sandbox import PortAllocator, TargetProcess

LOGIN = {"path": "/api/login", "json": {"username": "alice", "password": "alice123"}}
AUTH = {"Authorization": "Bearer tok-1"}

CASES = [
    # --- 1. SQL injection: parameterize the LIKE query -------------------------------
    (Exploit("GET", "/api/products/search", None, {"q": "' OR 1=1--"}, None,
             "FLAG{sqli_product_dump}", "sqli", None),
     [Edit("app/routes/products.py",
           '    query = (f"SELECT id, name, price, internal_note FROM products "\n'
           '             f"WHERE archived = 0 AND name LIKE \'%{q}%\'")\n',
           '    query = ("SELECT id, name, price, internal_note FROM products "\n'
           '             "WHERE archived = 0 AND name LIKE ?")\n'),
      Edit("app/routes/products.py",
           "    rows = [dict(r) for r in conn.execute(query).fetchall()]\n",
           "    rows = [dict(r) for r in conn.execute(query, (f\"%{q}%\",)).fetchall()]\n")]),

    # --- 2. IDOR on orders: scope to the caller --------------------------------------
    (Exploit("GET", "/api/orders/2", AUTH, None, None,
             "FLAG{idor_order_receipt}", "idor", LOGIN),
     [Edit("app/routes/orders.py",
           '    row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()\n',
           '    row = conn.execute("SELECT * FROM orders WHERE id=? AND user_id=?",\n'
           '                       (order_id, user["id"])).fetchone()\n')]),

    # --- 3. IDOR on support tickets ---------------------------------------------------
    (Exploit("GET", "/api/support/tickets/1", AUTH, None, None,
             "FLAG{idor_ticket_log}", "idor", LOGIN),
     [Edit("app/routes/tickets.py",
           '    row = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()\n',
           '    row = conn.execute("SELECT * FROM tickets WHERE id=? AND user_id=?",\n'
           '                       (ticket_id, user["id"])).fetchone()\n')]),

    # --- 4-5. Admin bypass: import + enforce the role on both admin routes ------------
    (Exploit("GET", "/api/admin/export", AUTH, None, None,
             "FLAG{admin_export_bypass}", "admin_bypass", LOGIN),
     [Edit("app/routes/admin.py",
           'from fastapi import APIRouter, Header\n',
           'from fastapi import APIRouter, Header, HTTPException\n'),
      Edit("app/routes/admin.py",
           'def export_all(authorization: str | None = Header(default=None)):\n'
           '    user = current_user(authorization)\n'
           '    if not user:\n'
           '        return {"error": "login required"}\n',
           'def export_all(authorization: str | None = Header(default=None)):\n'
           '    user = current_user(authorization)\n'
           '    if not user or user["role"] != "admin":\n'
           '        raise HTTPException(403, "admin only")\n')]),

    (Exploit("GET", "/api/admin/customers", AUTH, None, None,
             "FLAG{admin_customer_bypass}", "admin_bypass", LOGIN),
     [Edit("app/routes/admin.py",
           'def customers(authorization: str | None = Header(default=None)):\n'
           '    user = current_user(authorization)\n'
           '    if not user:\n'
           '        return {"error": "login required"}\n',
           'def customers(authorization: str | None = Header(default=None)):\n'
           '    user = current_user(authorization)\n'
           '    if not user or user["role"] != "admin":\n'
           '        raise HTTPException(403, "admin only")\n')]),

    # --- 6-7. Path traversal: resolve and contain on both file routes ----------------
    (Exploit("GET", "/api/downloads", None, {"file": "../secret.env"}, None,
             "FLAG{path_traversal_secret}", "path_traversal", None),
     [Edit("app/routes/downloads.py",
           'def download(file: str):\n'
           '    try:\n'
           '        return Path(_FILES / file).read_text(errors="replace")\n'
           '    except OSError as exc:\n'
           '        return {"error": str(exc)}\n',
           'def download(file: str):\n'
           '    base = _FILES.resolve()\n'
           '    target = (_FILES / file).resolve()\n'
           '    if target != base and base not in target.parents:\n'
           '        return {"error": "outside the library"}\n'
           '    try:\n'
           '        return target.read_text(errors="replace")\n'
           '    except OSError as exc:\n'
           '        return {"error": str(exc)}\n')]),

    (Exploit("GET", "/api/attachments", None, {"name": "../backup.sql"}, None,
             "FLAG{path_traversal_seed}", "path_traversal", None),
     [Edit("app/routes/attachments.py",
           'def attachment(name: str):\n'
           '    try:\n'
           '        return Path(_FILES / name).read_text(errors="replace")\n'
           '    except OSError as exc:\n'
           '        return {"error": str(exc)}\n',
           'def attachment(name: str):\n'
           '    base = _FILES.resolve()\n'
           '    target = (_FILES / name).resolve()\n'
           '    if target != base and base not in target.parents:\n'
           '        return {"error": "outside the library"}\n'
           '    try:\n'
           '        return target.read_text(errors="replace")\n'
           '    except OSError as exc:\n'
           '        return {"error": str(exc)}\n')]),

    # --- 8. Mass assignment on PUT /api/account: stop accepting role -----------------
    (Exploit("PUT", "/api/account", AUTH, None, {"role": "admin"},
             "FLAG{mass_assignment_role}", "mass_assignment", LOGIN),
     [Edit("app/routes/account.py",
           '    if body.display_name:\n'
           '        conn.execute("UPDATE users SET display_name=? WHERE id=?",\n'
           '                     (body.display_name, user["id"]))\n'
           '    if body.role:\n'
           '        conn.execute("UPDATE users SET role=? WHERE id=?", (body.role, user["id"]))\n'
           '    conn.commit()\n',
           '    if body.display_name:\n'
           '        conn.execute("UPDATE users SET display_name=? WHERE id=?",\n'
           '                     (body.display_name, user["id"]))\n'
           '    # role is never client-writable\n'
           '    if not body.display_name:\n'
           '        conn.execute("UPDATE users SET display_name=display_name WHERE id=?",\n'
           '                     (user["id"],))\n'
           '    conn.commit()\n')]),

    # --- 9. Mass assignment on PATCH /api/account/settings ---------------------------
    (Exploit("PATCH", "/api/account/settings", AUTH, None, {"is_admin": True},
             "FLAG{mass_assignment_admin}", "mass_assignment", LOGIN),
     [Edit("app/routes/account.py",
           '    if body.theme:\n'
           '        conn.execute("UPDATE users SET display_name=COALESCE(display_name,\'\') WHERE id=? "\n'
           '                     "-- theme storage placeholder", (user["id"],))\n'
           '    if body.is_admin is not None:\n'
           '        conn.execute("UPDATE users SET role=? WHERE id=?",\n'
           '                     ("admin" if body.is_admin else "user", user["id"]))\n'
           '    conn.commit()\n',
           '    if body.theme:\n'
           '        conn.execute("UPDATE users SET display_name=COALESCE(display_name,\'\') WHERE id=? "\n'
           '                     "-- theme storage placeholder", (user["id"],))\n'
           '    # is_admin is never client-writable\n'
           '    conn.commit()\n')]),

    # --- 10. Debug endpoint: require an admin session --------------------------------
    (Exploit("GET", "/api/debug/env", None, None, None,
             "FLAG{debug_env_leak}", "debug_exposure", None),
     [Edit("app/routes/debug.py",
           'from fastapi import APIRouter\n',
           'from fastapi import APIRouter, Header, HTTPException\n\n'
           'from app.routes.auth import current_user\n'),
      Edit("app/routes/debug.py",
           'def debug_env():\n',
           'def debug_env(authorization: str | None = Header(default=None)):\n'
           '    user = current_user(authorization)\n'
           '    if not user or user["role"] != "admin":\n'
           '        raise HTTPException(403, "admin only")\n')]),

    # --- 11. Code injection: ast whitelist instead of eval --------------------------
    (Exploit("GET", "/api/widgets/preview", None, {"expr": "[v for v in globals().values()"
             " if 'FLAG{' in str(v)]"}, None,
             "FLAG{code_injection_eval}", "code_injection", None),
     [Edit("app/routes/widgets.py",
           'try:\n'
           '        result = eval(expr)  # noqa: S307 - demo vulnerability\n'
           '        return {"expr": expr, "preview": str(result)}\n'
           '    except Exception as exc:  # any failure still echoes the reason back to the client\n'
           '        return {"expr": expr, "error": str(exc)}\n',
           '    try:\n'
           '        node = ast.parse(expr, mode="eval")\n'
           '    except SyntaxError as exc:\n'
           '        return {"expr": expr, "error": f"not an expression: {exc}"}\n'
           '    allowed = (ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp,\n'
           '               ast.operator, ast.unaryop, ast.Add, ast.Sub, ast.Mult, ast.Div,\n'
           '               ast.USub, ast.UAdd, ast.Load, ast.Num)\n'
           '    for sub in ast.walk(node):\n'
           '        if type(sub).__name__ in ("Name", "Call", "Attribute", "Subscript"):\n'
           '            return {"expr": expr, "error": "only numbers and arithmetic are allowed"}\n'
           '        if not isinstance(sub, allowed):\n'
           '            return {"expr": expr, "error": "only numbers and arithmetic are allowed"}\n'
           '    code = compile(node, "<widget>", "eval")\n'
           '    result = {}  # evaluation sandbox: constants only, no names resolve\n'
           '    import operator as _op\n'
           '    ops = {ast.Add: _op.add, ast.Sub: _op.sub, ast.Mult: _op.mul, ast.Div: _op.truediv}\n'
           '    try:\n'
           '        def _ev(n):\n'
           '            if isinstance(n, ast.Constant):\n'
           '                return n.value\n'
           '            if isinstance(n, ast.BinOp):\n'
           '                return ops[type(n.op)](_ev(n.left), _ev(n.right))\n'
           '            if isinstance(n, ast.UnaryOp):\n'
           '                return (-_ev(n.operand) if isinstance(n.op, ast.USub) else _ev(n.operand))\n'
           '            raise ValueError("unsupported")\n'
           '        result = {"preview": str(_ev(node.body))}\n'
           '    except Exception as exc:\n'
           '        return {"expr": expr, "error": str(exc)}\n'
           '    return {"expr": expr, **result}\n'),
      Edit("app/routes/widgets.py",
           'from fastapi import APIRouter\n',
           'import ast\n'
           '\n'
           'from fastapi import APIRouter\n')]),
]


def main() -> None:
    cfg = load_config("arena.demo.yaml")
    cache = cfg.cache_path
    ports = PortAllocator(8300)
    work = Path("work/demo-cache-build")
    live = TargetProcess(cfg.app_dir, cfg.seed_db, ports.next(), work, cfg.app_module,
                         cfg.extra_paths)
    live.prepare()
    live.start()
    openapi = httpx.get(live.url + "/openapi.json", timeout=5).json()
    assert openapi, "no openapi from the target"
    ok = failed = 0
    try:
        for i, (ex, edits) in enumerate(CASES, 1):
            res, reason = _stage_and_verify(edits, live.dir, cfg.seed_db, ex,
                                            cfg.functional_tests, ports, work, lambda e: None,
                                            cfg.app_module, cfg.extra_paths)
            if res:
                store_edits(cache, ex, edits)
                res.new_target.stop()
                ok += 1
                print(f"[{i:02d}] OK   {ex.vuln_class:<16} {ex.path}")
            else:
                failed += 1
                print(f"[{i:02d}] FAIL {ex.vuln_class:<16} {ex.path}\n      {reason}")
    finally:
        live.stop()
        if Path("work/demo-cache-build").exists():
            shutil.rmtree("work/demo-cache-build", ignore_errors=True)
    print(f"\ncache build: {ok} stored, {failed} failed -> {cache}")


if __name__ == "__main__":
    from pathlib import Path
    import shutil
    main()
