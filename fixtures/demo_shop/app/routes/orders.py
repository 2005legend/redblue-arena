from fastapi import APIRouter, Header

from app.db import get_conn
from app.routes.auth import current_user

router = APIRouter()


# IDOR (class: idor): the handler trusts the identifier and never checks that the order
# belongs to the caller, so any signed-in user can read anyone's receipt text.
# Order 2 is bob's and its receipt text carries FLAG{idor_order_receipt}.
# FIX: fetch with "WHERE id=? AND user_id=?" (or 404/403 when it is someone else's).
@router.get("/api/orders")
def my_orders(authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"error": "login required"}
    conn = get_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM orders WHERE user_id=?",
                                          (user["id"],)).fetchall()]
    conn.close()
    return {"orders": rows}


@router.get("/api/orders/{order_id}")
def get_order(order_id: int, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"error": "login required"}
    conn = get_conn()
    row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    conn.close()
    if not row:
        return {"error": "order not found"}
    return dict(row)
