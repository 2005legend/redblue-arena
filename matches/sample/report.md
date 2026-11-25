# Vibe Arena security report

## sqli: `GET /api/search`

- Leaked: `FLAG{sqli_leaked_db}`
- Time to patch: 6.9 s
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
+        rows = conn.execute(sql, ('%' + q + '%',)).fetchall()
     except Exception as exc:
         raise HTTPException(500, f"query failed: {exc}")
     finally:
```

## idor: `GET /api/invoices/3`

- Leaked: `FLAG{idor_invoice_leak}`
- Time to patch: 7.3 s
- Exploit replay after the fix: blocked

```diff
--- a/app/routes/invoices.py
+++ b/app/routes/invoices.py
@@ -32,10 +32,10 @@
 
 @router.get("/api/invoices/{invoice_id}")
 def get_invoice(invoice_id: int, authorization: str | None = Header(default=None)):
-    current_user(authorization)
+    user = current_user(authorization)
     conn = get_conn()
     row = conn.execute(
-        "SELECT id, owner_id, amount, note FROM invoices WHERE id = ?", (invoice_id,)
+        "SELECT id, owner_id, amount, note FROM invoices WHERE id = ? AND owner_id = ?", (invoice_id, user["id"])
     ).fetchone()
     conn.close()
     if row is None:
```

## admin_bypass: `GET /api/admin/export`

- Leaked: `FLAG{admin_export_bypass}`
- Time to patch: 7.4 s
- Exploit replay after the fix: blocked

```diff
--- a/app/routes/admin.py
+++ b/app/routes/admin.py
@@ -8,7 +8,8 @@
 
 @router.get("/api/admin/export")
 def export_all(authorization: str | None = Header(default=None)):
-    current_user(authorization)
+    user = current_user(authorization)
+    assert user["role"] == "admin", "admin only"
     conn = get_conn()
     users = [dict(r) for r in conn.execute("SELECT id, username, role FROM users")]
     notes = [dict(r) for r in conn.execute(
```

## path_traversal: `GET /api/files`

- Leaked: `FLAG{path_traversal_leak}`
- Time to patch: 7.0 s
- Exploit replay after the fix: blocked

```diff
--- a/app/routes/files.py
+++ b/app/routes/files.py
@@ -7,7 +7,10 @@
 
 @router.get("/api/files")
 def get_file(name: str):
-    path = Path("files") / name
+    base = Path("files").resolve()
+    path = (base / name).resolve()
+    if base not in path.parents:
+        raise HTTPException(404, "not found")
     if not path.is_file():
         raise HTTPException(404, "not found")
     return {"name": name, "content": path.read_text()}
```

## mass_assignment: `PUT /api/profile`

- Leaked: `FLAG{mass_assignment_leak}`
- Time to patch: 7.0 s
- Exploit replay after the fix: blocked

```diff
--- a/app/routes/profile.py
+++ b/app/routes/profile.py
@@ -19,8 +19,7 @@
     if body.display_name is not None:
         conn.execute("UPDATE users SET display_name = ? WHERE id = ?",
                      (body.display_name, user["id"]))
-    if body.role is not None:
-        conn.execute("UPDATE users SET role = ? WHERE id = ?", (body.role, user["id"]))
+            # role is not client-writable
     conn.commit()
     row = conn.execute(
         "SELECT id, username, display_name, role FROM users WHERE id = ?", (user["id"],)
```

## debug_exposure: `GET /api/debug/config`

- Leaked: `FLAG{debug_config_leak}`
- Time to patch: 6.8 s
- Exploit replay after the fix: blocked

```diff
--- a/app/routes/debug.py
+++ b/app/routes/debug.py
@@ -1,6 +1,8 @@
 from pathlib import Path
 
-from fastapi import APIRouter
+from fastapi import APIRouter, Header, HTTPException
+from pathlib import Path
+from app.routes.auth import current_user
 
 router = APIRouter()
 
@@ -8,5 +10,8 @@
 
 
 @router.get("/api/debug/config")
-def debug_config():
+def debug_config(authorization: str | None = Header(default=None)):
+    user = current_user(authorization)
+    if user["role"] != "admin":
+        raise HTTPException(403, "admin only")
     return {"debug": True, "secret": _SECRET}
```

## code_injection: `GET /api/calc`

- Leaked: `FLAG{code_injection_leak}`
- Time to patch: 6.5 s
- Exploit replay after the fix: blocked

```diff
--- a/app/routes/calc.py
+++ b/app/routes/calc.py
@@ -9,6 +9,36 @@
 
 @router.get("/api/calc")
 def calc(expr: str = "1+1"):
+    import ast
+    import operator
+
+    def safe_eval(node):
+        if isinstance(node, ast.Expression):
+            return safe_eval(node.body)
+        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
+            return node.value
+        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
+            return operator.neg(safe_eval(node.operand)) if isinstance(node.op, ast.USub) else safe_eval(node.operand)
+        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
+            left = safe_eval(node.left)
+            right = safe_eval(node.right)
+            if isinstance(node.op, ast.Add):
+                return operator.add(left, right)
+            elif isinstance(node.op, ast.Sub):
+                return operator.sub(left, right)
+            elif isinstance(node.op, ast.Mult):
+                return operator.mul(left, right)
+            elif isinstance(node.op, ast.Div):
+                return operator.truediv(left, right)
+        else:
+            raise HTTPException(400, "Invalid expression")
+
+    try:
+        tree = ast.parse(expr, mode="eval")
+        result = safe_eval(tree)
+        return {"expr": expr, "result": str(result)}
+    except Exception as exc:
+        raise HTTPException(400, str(exc))
     try:
         return {"expr": expr, "result": str(eval(expr))}
     except Exception as exc:
```
