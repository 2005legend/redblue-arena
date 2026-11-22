from fastapi import APIRouter, Header, HTTPException

from app.db import get_conn
from app.routes.auth import current_user

router = APIRouter()


@router.get("/api/search")
def search(q: str = ""):
    conn = get_conn()
    sql = f"SELECT id, name FROM products WHERE hidden = 0 AND name LIKE '%{q}%'"
    try:
        rows = conn.execute(sql).fetchall()
    except Exception as exc:
        raise HTTPException(500, f"query failed: {exc}")
    finally:
        conn.close()
    return [dict(r) for r in rows]


@router.get("/api/invoices")
def list_invoices(authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, amount, note FROM invoices WHERE owner_id = ?", (user["id"],)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/api/invoices/{invoice_id}")
def get_invoice(invoice_id: int, authorization: str | None = Header(default=None)):
    current_user(authorization)
    conn = get_conn()
    row = conn.execute(
        "SELECT id, owner_id, amount, note FROM invoices WHERE id = ?", (invoice_id,)
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(404, "not found")
    return dict(row)
