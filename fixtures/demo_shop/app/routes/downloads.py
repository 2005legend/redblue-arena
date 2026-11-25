from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

_FILES = Path(__file__).resolve().parents[2] / "files"


# PATH TRAVERSAL (class: path_traversal): the requested name is joined onto the files
# directory with no containment check, so `../../secret.env` walks out of the sandbox
# root and returns whatever the process can read. server.env carries
# FLAG{path_traversal_secret}; the same flaw also lives in attachments.py.
# FIX: base = _FILES.resolve(); target = (base / name).resolve();
#      if base not in target.parents and target != base: reject.
@router.get("/api/downloads")
def download(file: str):
    try:
        return Path(_FILES / file).read_text(errors="replace")
    except OSError as exc:
        return {"error": str(exc)}
