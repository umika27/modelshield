"""
Quick DB inspector — run this AFTER demo_shyalona_module.py to check that
data actually landed in the database. Uses a real file (not :memory:) so
you can open it in a viewer too.

Usage:
    python inspect_db.py
"""

import sqlite3

conn = sqlite3.connect("modelshield.db")
conn.row_factory = sqlite3.Row

for table in ["models", "evaluations", "failures", "capsules", "regression_tests"]:
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    print(f"\n=== {table} ({len(rows)} rows) ===")
    for row in rows:
        print(dict(row))

conn.close()
