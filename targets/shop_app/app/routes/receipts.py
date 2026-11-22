import os
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..db import get_db
from ..deps import current_user

router = APIRouter(prefix="/api")

RECEIPTS_DIR = "receipts"


@router.get("/receipts/{filename}")
def download_receipt(filename: str, user: dict = Depends(current_user),
                     db: sqlite3.Connection = Depends(get_db)):
    # Serve only a file recorded on one of the caller's own orders
    # (admins may fetch any recorded receipt).
    if user["role"] == "admin":
        row = db.execute("SELECT 1 FROM orders WHERE receipt_file = ?",
                         (filename,)).fetchone()
    else:
        row = db.execute(
            "SELECT 1 FROM orders WHERE receipt_file = ? AND user_id = ?",
            (filename, user["id"])).fetchone()
    if row is None:
        raise HTTPException(404, "Receipt not found")
    base = os.path.realpath(RECEIPTS_DIR)
    path = os.path.realpath(os.path.join(base, filename))
    if os.path.dirname(path) != base or not os.path.isfile(path):
        raise HTTPException(404, "Receipt not found")
    return FileResponse(path, media_type="text/plain", filename=os.path.basename(path))
