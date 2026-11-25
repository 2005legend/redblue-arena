import sqlite3

from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.db import get_conn

router = APIRouter()


class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/api/login")
def login(body: LoginBody):
    conn = get_conn()
    row = conn.execute("SELECT id, username, role FROM users WHERE username=? AND password=?",
                       (body.username, body.password)).fetchone()
    conn.close()
    if not row:
        return {"error": "bad credentials"}
    return {"token": f"tok-{row['id']}", "username": row["username"], "role": row["role"]}


def current_user(authorization: str | None) -> dict | None:
    if not authorization:
        return None
    token = authorization.split(" ")[-1]
    if not token.startswith("tok-"):
        return None
    try:
        user_id = int(token[4:])
    except ValueError:
        return None
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
