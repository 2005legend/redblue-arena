from fastapi import APIRouter, Header

from app.db import get_conn
from app.routes.auth import current_user

router = APIRouter()


@router.get("/api/admin/export")
def export_all(authorization: str | None = Header(default=None)):
    current_user(authorization)
    conn = get_conn()
    users = [dict(r) for r in conn.execute("SELECT id, username, role FROM users")]
    notes = [dict(r) for r in conn.execute("SELECT key, value FROM config")]
    conn.close()
    return {"users": users, "config": notes}
