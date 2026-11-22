"""Builds matches/sample.jsonl from REAL fixes applied to the dev target (so the diffs are genuine).
The events themselves are hand-authored for UI development and are marked sample=true."""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from arena.blue import apply_edits, make_patch, parse_edits  # noqa: E402
from arena.exporter import export  # noqa: E402
from arena.referee import Exploit  # noqa: E402


def blk(path, search, replace):
    return f"FILE: {path}\n<<<<<<< SEARCH\n{search}\n=======\n{replace}\n>>>>>>> REPLACE\n"


SQL_OLD = ("    sql = f\"SELECT id, name FROM products WHERE hidden = 0 AND name LIKE '%{q}%'\"\n"
           "    try:\n        rows = conn.execute(sql).fetchall()")
SQL_NEW = ("    sql = \"SELECT id, name FROM products WHERE hidden = 0 AND name LIKE ?\"\n"
           "    try:\n        rows = conn.execute(sql, (f\"%{q}%\",)).fetchall()")
IDOR_OLD = ('    current_user(authorization)\n    conn = get_conn()\n    row = conn.execute(\n'
            '        "SELECT id, owner_id, amount, note FROM invoices WHERE id = ?", (invoice_id,)')
IDOR_NEW = ('    user = current_user(authorization)\n    conn = get_conn()\n    row = conn.execute(\n'
            '        "SELECT id, owner_id, amount, note FROM invoices WHERE id = ? AND owner_id = ?",\n'
            '        (invoice_id, user["id"])')
ADM_OLD = "    current_user(authorization)\n    conn = get_conn()\n    users ="
ADM_NEW = ('    user = current_user(authorization)\n    if user["role"] != "admin":\n'
           '        raise HTTPException(403, "admin only")\n    conn = get_conn()\n    users =')

TRAV_OLD = '    path = Path("files") / name\n    if not path.is_file():'
TRAV_NEW = ('    base = Path("files").resolve()\n    path = (base / name).resolve()\n'
            '    if base not in path.parents or not path.is_file():')

FIXES = [
    ("sqli", "/api/search", blk("app/routes/invoices.py", SQL_OLD, SQL_NEW)),
    ("idor", "/api/invoices/{id}", blk("app/routes/invoices.py", IDOR_OLD, IDOR_NEW)),
    ("admin_bypass", "/api/admin/export",
     blk("app/routes/admin.py", "from fastapi import APIRouter, Header\n",
         "from fastapi import APIRouter, Header, HTTPException\n")
     + blk("app/routes/admin.py", ADM_OLD, ADM_NEW)),
    ("path_traversal", "/api/files", blk("app/routes/files.py", TRAV_OLD, TRAV_NEW)),
]
EXPLOITS = [
    Exploit("GET", "/api/search", None, {"q": "' OR 1=1--"}, None, "FLAG{sqli_leaked_db}", "sqli"),
    Exploit("GET", "/api/invoices/3", {"Authorization": "Bearer tok-1"}, None, None,
            "FLAG{idor_invoice_leak}", "idor"),
    Exploit("GET", "/api/admin/export", {"Authorization": "Bearer tok-1"}, None, None,
            "FLAG{admin_export_bypass}", "admin_bypass"),
    Exploit("GET", "/api/files", None, {"name": "../secret.txt"}, None,
            "FLAG{path_traversal_leak}", "path_traversal"),
]
TTPS = [9.2, 11.4, 8.1, 10.3]

work = Path(tempfile.mkdtemp())
shutil.copytree(ROOT / "fixtures" / "dev_target" / "app", work / "cur" / "app")
patches = []
for _, _, edits in FIXES:
    shutil.rmtree(work / "before", ignore_errors=True)
    shutil.copytree(work / "cur", work / "before")
    apply_edits(work / "cur", parse_edits(edits))
    patches.append(make_patch(work / "before", work / "cur"))

ev, t = [], [0.0]


def add(dt, **e):
    t[0] = round(t[0] + dt, 2)
    ev.append(dict(e, seq=len(ev), ts=t[0]))


add(0, type="match_start", sample=True,
    routes=["/api/login", "/api/search", "/api/invoices", "/api/invoices/{id}", "/api/admin/export", "/api/files"])
add(0.5, type="health", passed=6, failed=0)
red = blue = 0
for i, (ex, patch, ttp) in enumerate(zip(EXPLOITS, patches, TTPS)):
    route = FIXES[i][1]
    add(1.0, type="red_action", tool="discover_routes", args={}, status=None)
    add(1.2, type="red_action", tool="send_http_request", status=200,
        args={"method": ex.method, "path": ex.path, "params": ex.params})
    red += 1
    add(0.6, type="breach", route=route, vuln_class=ex.vuln_class, flag=ex.flag, path=ex.path)
    add(0.1, type="score", red=red, blue=blue)
    add(1.0, type="blue_thinking", text=f"Root cause in {route}: {ex.vuln_class}. Drafting a minimal fix.")
    add(ttp / 2, type="blue_attempt", n=1, ok=True, reason="verified")
    blue += 1
    add(0.5, type="patched", route=route, vuln_class=ex.vuln_class, patch=patch, ttp_seconds=ttp)
    add(0.1, type="score", red=red, blue=blue)
    add(0.4, type="health", passed=6, failed=0)
add(1.0, type="match_end", files=["hardened.patch", "report.md"],
    summary=dict(red=4, blue=4, closed=4, total=4, tokens=24106, ttp=TTPS))
(ROOT / "matches").mkdir(exist_ok=True)
(ROOT / "matches" / "sample.jsonl").write_text("\n".join(json.dumps(e) for e in ev) + "\n")
export(ROOT / "matches" / "sample", EXPLOITS, patches, TTPS)
print("sample written:", len(ev), "events")
