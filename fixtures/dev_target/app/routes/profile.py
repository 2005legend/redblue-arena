from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.db import get_conn
from app.routes.auth import current_user

router = APIRouter()


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    role: str | None = None


@router.put("/api/profile")
def update_profile(body: ProfileUpdate, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    conn = get_conn()
    if body.display_name is not None:
        conn.execute("UPDATE users SET display_name = ? WHERE id = ?",
                     (body.display_name, user["id"]))
    if body.role is not None:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (body.role, user["id"]))
    conn.commit()
    row = conn.execute(
        "SELECT id, username, display_name, role FROM users WHERE id = ?", (user["id"],)
    ).fetchone()
    result = {"user": dict(row)}
    if row["role"] == "admin":
        note = conn.execute(
            "SELECT value FROM config WHERE key = 'profile_admin_note'").fetchone()
        result["admin_note"] = note["value"] if note else None
    conn.close()
    return result
