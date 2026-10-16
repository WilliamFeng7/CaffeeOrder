#!/usr/bin/env python3
"""Copy menu products into a fresh demo database, without users or orders."""
import sqlite3
import sys
from pathlib import Path

source, destination = map(Path, sys.argv[1:])
if destination.exists():
    raise SystemExit("Refusing to overwrite an existing database")
with sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True) as original:
    schema = original.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='menuitem'"
    ).fetchone()[0]
    products = original.execute("SELECT * FROM menuitem").fetchall()
    if not products:
        raise SystemExit("Source menu is empty")
    with sqlite3.connect(destination) as demo:
        demo.execute(schema)
        placeholders = ",".join("?" for _ in products[0])
        demo.executemany(f"INSERT INTO menuitem VALUES ({placeholders})", products)
print(f"Prepared {len(products)} menu products; no user or order data copied.")
