import sqlite3

from fastapi import Depends, Header, HTTPException

from .db import get_db


def current_user(authorization: str | None = Header(default=None),
                 db: sqlite3.Connection = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization[7:].strip()
    row = db.execute(
        "SELECT u.id, u.username, u.role FROM tokens t "
        "JOIN users u ON u.id = t.user_id WHERE t.token = ?", (token,)
    ).fetchone()
    if row is None:
        raise HTTPException(401, "Invalid token")
    return dict(row)


def admin_user(user: dict = Depends(current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return user
