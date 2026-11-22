import os
import sqlite3
import sys

from app.security import hash_password

SCHEMA = """
CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL, role TEXT NOT NULL);
CREATE TABLE tokens (token TEXT PRIMARY KEY, user_id INTEGER NOT NULL);
CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL,
  description TEXT NOT NULL, price REAL NOT NULL);
CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL, quantity INTEGER NOT NULL, total REAL NOT NULL,
  receipt_file TEXT);
"""

USERS = [(1, "alice", "alice123", "customer"), (2, "bob", "bob123", "customer"),
         (3, "admin", "admin123", "admin")]
PRODUCTS = [
    (1, "Espresso Mug", "Ceramic mug for espresso", 8.50),
    (2, "Travel Tumbler", "Insulated steel tumbler", 22.00),
    (3, "Notebook", "A5 dotted notebook", 6.25),
    (4, "Desk Lamp", "LED desk lamp with dimmer", 34.90),
    (5, "Wireless Mouse", "Ergonomic wireless mouse", 19.99),
    (6, "Backpack", "Water resistant 20L backpack", 49.00),
]
# (id, user_id, product_id, quantity, total, receipt_file)
ORDERS = [
    (1, 1, 1, 2, 17.00, "receipt_1001.txt"),
    (2, 1, 3, 1, 6.25, None),
    (3, 2, 4, 1, 34.90, "receipt_1002.txt"),
    (4, 2, 5, 2, 39.98, "receipt_1003.txt"),
]
RECEIPTS = {
    "receipt_1001.txt": "Receipt 1001\nCustomer: alice\nEspresso Mug x2  17.00\nTotal: 17.00\n",
    "receipt_1002.txt": "Receipt 1002\nCustomer: bob\nDesk Lamp x1  34.90\nTotal: 34.90\n",
    "receipt_1003.txt": "Receipt 1003\nCustomer: bob\nWireless Mouse x2  39.98\nTotal: 39.98\n",
}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "seed.db"
    if os.path.exists(out):
        os.remove(out)
    conn = sqlite3.connect(out)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO users VALUES (?,?,?,?)",
                     [(i, u, hash_password(p), r) for i, u, p, r in USERS])
    conn.executemany("INSERT INTO products VALUES (?,?,?,?)", PRODUCTS)
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", ORDERS)
    conn.commit()
    conn.close()
    os.makedirs("receipts", exist_ok=True)
    for name, text in RECEIPTS.items():
        with open(os.path.join("receipts", name), "w", encoding="utf-8") as f:
            f.write(text)
    print("seeded", out)


if __name__ == "__main__":
    main()
