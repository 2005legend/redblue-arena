import os
import sqlite3


def db_path() -> str:
    return os.environ.get("ARENA_DB", "seed.db")


def get_db():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
