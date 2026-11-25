import os
import sqlite3
from pathlib import Path


def get_conn() -> sqlite3.Connection:
    db = os.environ.get("ARENA_DB", "./seed.db")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn
