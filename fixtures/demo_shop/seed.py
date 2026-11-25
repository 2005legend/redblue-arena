"""Build the demo-shop database: python seed.py (also run automatically on first boot)."""
import os
import sqlite3

DB = os.environ.get("ARENA_DB", "seed.db")

USERS = [
    (1, "alice", "alice123", "user", "Alice"),
    (2, "bob", "bob123", "user", "Bob"),
    (3, "carol", "carol123", "user", "Carol"),
    (4, "admin", "admin123", "admin", "Ops"),
]

PRODUCTS = [
    (1, "Aeropress Go", 39.0, 0, ""),
    (2, "Chemex 6-cup", 48.0, 0, ""),
    (3, "Hand grinder S2", 89.0, 0, ""),
    (4, "Columbia roast 250g", 14.0, 0, ""),
    (5, "Prototype batch 0x1", 1.0, 1, "internal sample - never list: FLAG{sqli_product_dump}"),
]

ORDERS = [
    (1, 1, 1, 39.0, "Aeropress Go ships in 2 days. Standard receipt."),
    (2, 2, 2, 48.0, "Gift wrap + note to wife: FLAG{idor_order_receipt}"),
    (3, 3, 2, 48.0, "Corporate purchase, acct LUMEN-4411, budget code FLAG-retained. "
                    "_private_ledger_ref HQ-9012"),
]

TICKETS = [
    (1, 3, "Refund stuck", "ops note: card token tok_live_9d11 + FLAG{idor_ticket_log} — do not expose"),
    (2, 1, "Where is my grinder?", "shipped Tuesday"),
]

conn = sqlite3.connect(DB)
conn.executescript(
    """
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS tickets;
    CREATE TABLE users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT,
        role TEXT DEFAULT 'user', display_name TEXT
    );
    CREATE TABLE products (
        id INTEGER PRIMARY KEY, name TEXT, price REAL, archived INTEGER DEFAULT 0,
        internal_note TEXT DEFAULT ''
    );
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER,
        total REAL, receipt_text TEXT
    );
    CREATE TABLE tickets (
        id INTEGER PRIMARY KEY, user_id INTEGER, subject TEXT, status TEXT
    );
    """
)
conn.executemany("INSERT INTO users VALUES (?,?,?,?,?)", USERS)
conn.executemany("INSERT INTO products VALUES (?,?,?,?,?)", PRODUCTS)
conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", ORDERS)
conn.executemany("INSERT INTO tickets VALUES (?,?,?,?)", TICKETS)
conn.commit()
conn.close()
print(f"seeded {DB}")
