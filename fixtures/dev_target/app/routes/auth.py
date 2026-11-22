from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_conn

router = APIRouter()


class Login(BaseModel):
    username: str
    password: str


def current_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer tok-"):
        raise HTTPException(401, "login required")
    uid = authorization.removeprefix("Bearer tok-")
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(401, "bad token")
    return dict(row)


@router.post("/api/login")
def login(body: Login):
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        (body.username, body.password),
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(401, "invalid credentials")
    return {"token": f"tok-{row['id']}"}
