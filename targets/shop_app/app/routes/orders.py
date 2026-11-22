import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..db import get_db
from ..deps import current_user

router = APIRouter(prefix="/api")

COLS = "id, product_id, quantity, total, receipt_file"


class OrderIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=100)


@router.get("/orders")
def list_orders(user: dict = Depends(current_user),
                db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(f"SELECT {COLS} FROM orders WHERE user_id = ? ORDER BY id",
                      (user["id"],)).fetchall()
    return [dict(r) for r in rows]


@router.get("/orders/{order_id}")
def get_order(order_id: int, user: dict = Depends(current_user),
              db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(f"SELECT {COLS} FROM orders WHERE id = ? AND user_id = ?",
                     (order_id, user["id"])).fetchone()
    if row is None:
        raise HTTPException(404, "Order not found")
    return dict(row)


@router.post("/orders", status_code=201)
def create_order(body: OrderIn, user: dict = Depends(current_user),
                 db: sqlite3.Connection = Depends(get_db)):
    prod = db.execute("SELECT price FROM products WHERE id = ?",
                      (body.product_id,)).fetchone()
    if prod is None:
        raise HTTPException(404, "Product not found")
    total = round(prod["price"] * body.quantity, 2)
    cur = db.execute(
        "INSERT INTO orders (user_id, product_id, quantity, total) VALUES (?,?,?,?)",
        (user["id"], body.product_id, body.quantity, total),
    )
    db.commit()
    return {"id": cur.lastrowid, "product_id": body.product_id,
            "quantity": body.quantity, "total": total, "receipt_file": None}
