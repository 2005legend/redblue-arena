import sqlite3

from fastapi import APIRouter, Depends

from ..db import get_db

router = APIRouter(prefix="/api")

ESC = "\\"


@router.get("/search")
def search(q: str = "", db: sqlite3.Connection = Depends(get_db)):
    q = q.replace(ESC, ESC + ESC).replace("%", ESC + "%").replace("_", ESC + "_")
    like = "%" + q + "%"
    rows = db.execute(
        "SELECT id, name, description, price FROM products "
        "WHERE name LIKE ? ESCAPE ? OR description LIKE ? ESCAPE ? "
        "ORDER BY id LIMIT 50",
        (like, ESC, like, ESC),
    ).fetchall()
    return [dict(r) for r in rows]
