from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.db import get_conn
from app.routes.auth import current_user

router = APIRouter()


class ProfileBody(BaseModel):
    display_name: str | None = None
    role: str | None = None          # never client-writable in a sane app


class SettingsBody(BaseModel):
    theme: str | None = None
    is_admin: bool | None = None     # never client-writable in a sane app


# MASS ASSIGNMENT (class: mass_assignment): the body is copied straight into the update,
# so {"role": "admin"} self-promotes and the response spills the canary.
# FIX: whitelist display_name only - never accept role / is_admin from a client.
@router.put("/api/account")
def update_profile(body: ProfileBody, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"error": "login required"}
    conn = get_conn()
    if body.display_name:
        conn.execute("UPDATE users SET display_name=? WHERE id=?",
                     (body.display_name, user["id"]))
    if body.role:
        conn.execute("UPDATE users SET role=? WHERE id=?", (body.role, user["id"]))
    conn.commit()
    row = conn.execute("SELECT id, username, role, display_name FROM users WHERE id=?",
                       (user["id"],)).fetchone()
    conn.close()
    out = dict(row)
    if out["role"] == "admin":
        out["note"] = "privileges escalated to admin FLAG{mass_assignment_role}"
    return out


# MASS ASSIGNMENT (class: mass_assignment), second instance on the settings route.
@router.patch("/api/account/settings")
def update_settings(body: SettingsBody, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"error": "login required"}
    conn = get_conn()
    if body.theme:
        conn.execute("UPDATE users SET display_name=COALESCE(display_name,'') WHERE id=? "
                     "-- theme storage placeholder", (user["id"],))
    if body.is_admin is not None:
        conn.execute("UPDATE users SET role=? WHERE id=?",
                     ("admin" if body.is_admin else "user", user["id"]))
    conn.commit()
    row = conn.execute("SELECT id, username, role FROM users WHERE id=?", (user["id"],)).fetchone()
    conn.close()
    out = dict(row)
    if out["role"] == "admin":
        out["note"] = "settings saved with elevated rights FLAG{mass_assignment_admin}"
    return out
