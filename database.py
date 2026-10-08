"""Create a small SQLite database and load illustrative demo shop rows."""
import json
import os
import sqlite3
from pathlib import Path

SOURCE_DATA_DIR = Path(__file__).parent / "data"
DATA_DIR = Path(os.environ.get("WINE_DATA_DIR", str(SOURCE_DATA_DIR)))
DB_PATH = DATA_DIR / "wines.db"


def connect(read_only=False):
    if read_only:
        db = sqlite3.connect(DB_PATH.resolve().as_uri() + "?mode=ro", uri=True)
    else:
        db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def initialize():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = connect()
    try:
        with db:
            db.execute("""CREATE TABLE IF NOT EXISTS wines (
                wine_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK(price_cents >= 0),
                vintage INTEGER, stock INTEGER NOT NULL CHECK(stock >= 0),
                attributes TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY, payload TEXT NOT NULL
            )""")
            if db.execute("SELECT COUNT(*) FROM wines").fetchone()[0] == 0:
                catalog_path = DATA_DIR / "demo_wines.json"
                if not catalog_path.exists():
                    catalog_path = SOURCE_DATA_DIR / "demo_wines.json"
                rows = json.loads(catalog_path.read_text())
                for row in rows:
                    db.execute("INSERT INTO wines VALUES (?, ?, ?, ?, ?, ?)", (
                        row["wine_id"], row["name"], row["price_cents"],
                        row["vintage"], row["stock"], json.dumps(row["attributes"])))
    finally:
        db.close()
