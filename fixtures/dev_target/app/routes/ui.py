"""Serves the MiniShop storefront. The storefront is a plain client of the same
vulnerable API the arena attacks, so the bugs are unchanged by its presence."""
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

_INDEX = Path(__file__).with_name("static") / "index.html"


@router.get("/", include_in_schema=False)
def storefront():
    return FileResponse(_INDEX)
