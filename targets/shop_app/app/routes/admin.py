import sqlite3

from fastapi import APIRouter, Depends

from ..db import get_db
from ..deps import admin_user

router = APIRouter(prefix="/api/admin")

USERS_SQL = "SELECT id, username, role FROM users ORDER BY id"
ORDERS_SQL = ("SELECT id, user_id, product_id, quantity, total, receipt_file "
              "FROM orders ORDER BY id")


def _rows(db, sql):
    return [dict(r) for r in db.execute(sql).fetchall()]


@router.get("/users")
def users(_: dict = Depends(admin_user), db: sqlite3.Connection = Depends(get_db)):
    return _rows(db, USERS_SQL)


@router.get("/orders")
def all_orders(_: dict = Depends(admin_user), db: sqlite3.Connection = Depends(get_db)):
    return _rows(db, ORDERS_SQL)


@router.get("/export")
def export(_: dict = Depends(admin_user), db: sqlite3.Connection = Depends(get_db)):
    return {"users": _rows(db, USERS_SQL), "orders": _rows(db, ORDERS_SQL)}
