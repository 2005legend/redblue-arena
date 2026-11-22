import os
import sqlite3


def get_conn():
    conn = sqlite3.connect(os.environ.get("ARENA_DB", "seed.db"))
    conn.row_factory = sqlite3.Row
    return conn
