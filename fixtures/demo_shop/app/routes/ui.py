"""Serves the Lumen Goods storefront. A plain client of the same vulnerable API the arena
attacks, so the bugs are unchanged by its presence."""
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

_INDEX = Path(__file__).with_name("static") / "index.html"


@router.get("/", include_in_schema=False)
def storefront():
    return FileResponse(_INDEX)


@router.get("/api/products/list", include_in_schema=False)
def _public_list():
    """What the storefront grid displays: public rows only."""
    from app.db import get_conn
    conn = get_conn()
    rows = [{"id": r["id"], "name": r["name"], "price": r["price"]}
            for r in conn.execute(
                "SELECT id, name, price FROM products WHERE archived = 0").fetchall()]
    conn.close()
    return {"products": rows}
