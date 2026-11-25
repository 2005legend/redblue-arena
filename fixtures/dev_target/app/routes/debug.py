from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

_SECRET = Path(__file__).with_name("debug_secret.txt").read_text().strip()


@router.get("/api/debug/config")
def debug_config():
    return {"debug": True, "secret": _SECRET}
