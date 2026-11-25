from fastapi import APIRouter, Query

from app.db import get_conn

router = APIRouter()


# SQL INJECTION (class: sqli): the archived filter and the LIKE value are spliced into the
# query with an f-string, so `' OR 1=1--` (or `%' OR '1'='1`) drops the `archived = 0`
# guard and returns the prototype row, whose internal_note carries the canary.
# FIX: WHERE archived = 0 AND name LIKE ? with q passed as a bound parameter.
@router.get("/api/products/search")
def search(q: str = Query("")):
    conn = get_conn()
    query = (f"SELECT id, name, price, internal_note FROM products "
             f"WHERE archived = 0 AND name LIKE '%{q}%'")
    rows = [dict(r) for r in conn.execute(query).fetchall()]
    conn.close()
    return {"q": q, "results": rows}
