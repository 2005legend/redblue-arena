from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

_FILES = Path(__file__).resolve().parents[2] / "files"


# PATH TRAVERSAL (class: path_traversal), second instance: identical flaw to downloads.py
# on a different route. backup.sql holds FLAG{path_traversal_seed}.
# FIX: resolve against the files directory and refuse anything outside it.
@router.get("/api/attachments")
def attachment(name: str):
    try:
        return Path(_FILES / name).read_text(errors="replace")
    except OSError as exc:
        return {"error": str(exc)}
