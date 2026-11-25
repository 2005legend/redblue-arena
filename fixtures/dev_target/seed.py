import os
import sqlite3
import sys

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed.db")
if os.path.exists(path):
    os.remove(path)
c = sqlite3.connect(path)
c.executescript(
    """
CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, display_name TEXT);
CREATE TABLE invoices(id INTEGER PRIMARY KEY, owner_id INTEGER, amount REAL, note TEXT);
CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, hidden INTEGER);
CREATE TABLE config(key TEXT, value TEXT);
INSERT INTO users VALUES (1,'alice','alice123','user','Alice'),(2,'bob','bob123','user','Bob'),
  (3,'admin','admin123','admin','Admin');
INSERT INTO invoices VALUES (1,1,19.5,'alice coffee order'),(2,1,42.0,'alice tea order'),
  (3,2,99.0,'bob private invoice FLAG{idor_invoice_leak}');
INSERT INTO products VALUES (1,'coffee beans',0),(2,'green tea',0),(3,'espresso machine',0),
  (4,'internal FLAG{sqli_leaked_db}',1);
INSERT INTO config VALUES ('export_note','FLAG{admin_export_bypass}'),
  ('profile_admin_note','FLAG{mass_assignment_leak}');
"""
)
c.commit()
c.close()
