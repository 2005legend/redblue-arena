from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/api/files")
def get_file(name: str):
    path = Path("files") / name
    if not path.is_file():
        raise HTTPException(404, "not found")
    return {"name": name, "content": path.read_text()}
