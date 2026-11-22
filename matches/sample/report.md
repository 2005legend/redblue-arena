# Vibe Arena security report

## sqli: `GET /api/search`

- Leaked: `FLAG{sqli_leaked_db}`
- Time to patch: 9.2 s
- Exploit replay after the fix: blocked

```diff
--- a/app/routes/invoices.py
+++ b/app/routes/invoices.py
@@ -9,9 +9,9 @@
 @router.get("/api/search")
 def search(q: str = ""):
     conn = get_conn()
-    sql = f"SELECT id, name FROM products WHERE hidden = 0 AND name LIKE '%{q}%'"
+    sql = "SELECT id, name FROM products WHERE hidden = 0 AND name LIKE ?"
     try:
-        rows = conn.execute(sql).fetchall()
+        rows = conn.execute(sql, (f"%{q}%",)).fetchall()
     except Exception as exc:
         raise HTTPException(500, f"query failed: {exc}")
     finally:
```

## idor: `GET /api/invoices/3`

- Leaked: `FLAG{idor_invoice_leak}`
- Time to patch: 11.4 s
- Exploit replay after the fix: blocked

```diff
--- a/app/routes/invoices.py
+++ b/app/routes/invoices.py
@@ -32,10 +32,11 @@
 
 @router.get("/api/invoices/{invoice_id}")
 def get_invoice(invoice_id: int, authorization: str | None = Header(default=None)):
-    current_user(authorization)
+    user = current_user(authorization)
     conn = get_conn()
     row = conn.execute(
-        "SELECT id, owner_id, amount, note FROM invoices WHERE id = ?", (invoice_id,)
+        "SELECT id, owner_id, amount, note FROM invoices WHERE id = ? AND owner_id = ?",
+        (invoice_id, user["id"])
     ).fetchone()
     conn.close()
     if row is None:
```

## admin_bypass: `GET /api/admin/export`

- Leaked: `FLAG{admin_export_bypass}`
- Time to patch: 8.1 s
- Exploit replay after the fix: blocked

```diff
--- a/app/routes/admin.py
+++ b/app/routes/admin.py
@@ -1,4 +1,4 @@
-from fastapi import APIRouter, Header
+from fastapi import APIRouter, Header, HTTPException
 
 from app.db import get_conn
 from app.routes.auth import current_user
@@ -8,7 +8,9 @@
 
 @router.get("/api/admin/export")
 def export_all(authorization: str | None = Header(default=None)):
-    current_user(authorization)
+    user = current_user(authorization)
+    if user["role"] != "admin":
+        raise HTTPException(403, "admin only")
     conn = get_conn()
     users = [dict(r) for r in conn.execute("SELECT id, username, role FROM users")]
     notes = [dict(r) for r in conn.execute("SELECT key, value FROM config")]
```

## path_traversal: `GET /api/files`

- Leaked: `FLAG{path_traversal_leak}`
- Time to patch: 10.3 s
- Exploit replay after the fix: blocked

```diff
--- a/app/routes/files.py
+++ b/app/routes/files.py
@@ -7,7 +7,8 @@
 
 @router.get("/api/files")
 def get_file(name: str):
-    path = Path("files") / name
-    if not path.is_file():
+    base = Path("files").resolve()
+    path = (base / name).resolve()
+    if base not in path.parents or not path.is_file():
         raise HTTPException(404, "not found")
     return {"name": name, "content": path.read_text()}
```
