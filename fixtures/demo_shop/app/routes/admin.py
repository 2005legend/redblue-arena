from fastapi import APIRouter, Header

from app.db import get_conn
from app.routes.auth import current_user

router = APIRouter()


# ADMIN BYPASS (class: admin_bypass), two routes: both check that *a* session exists but
# never that its role is admin, so alice's token fulfils the guard.
# FIX: `if not user or user["role"] != "admin": return 403` (and check it on both routes).
@router.get("/api/admin/export")
def export_all(authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"error": "login required"}
    conn = get_conn()
    users = [dict(r) for r in conn.execute(
        "SELECT id, username, role, display_name FROM users").fetchall()]
    orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    return {"users": users, "order_count": orders,
            "note": "employee export — admins only FLAG{admin_export_bypass}"}


@router.get("/api/admin/customers")
def customers(authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"error": "login required"}
    conn = get_conn()
    rows = [dict(r) for r in conn.execute(
        "SELECT username, display_name FROM users WHERE role='user'").fetchall()]
    conn.close()
    return {"customers": rows,
            "note": "CRM dump — staff only FLAG{admin_customer_bypass}"}
