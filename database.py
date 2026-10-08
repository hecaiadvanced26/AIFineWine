"""SQLite catalog schema and imported finewine snapshot loading."""
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

SOURCE_DATA_DIR = Path(__file__).parent / "data"
DATA_DIR = Path(os.environ.get("WINE_DATA_DIR", str(SOURCE_DATA_DIR)))
DB_PATH = DATA_DIR / "wines.db"
CATALOG_PATH = SOURCE_DATA_DIR / "catalog.json"
CATALOG_COLUMNS = {
    "winery": "TEXT", "country": "TEXT", "region": "TEXT", "regional_style": "TEXT",
    "wine_type": "TEXT", "user_rating": "REAL", "community_avg_rating": "REAL",
    "user_review": "TEXT", "bottle_ml": "INTEGER", "inventory_synthetic": "INTEGER",
}


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def apply_catalog(db: sqlite3.Connection, snapshot: dict[str, Any]) -> None:
    """Replace catalog metadata, preserving stock for IDs already present and orders."""
    rows = snapshot["wines"]
    ids = [row["wine_id"] for row in rows]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Catalog must contain unique wine IDs")
    columns = ["wine_id", "name", "price_cents", "vintage", "stock", "attributes", *CATALOG_COLUMNS]
    updates = ",".join(f"{column}=excluded.{column}" for column in columns
                       if column not in {"wine_id", "stock"})
    placeholders = ",".join("?" for _ in columns)
    db.execute("DELETE FROM flavours")
    db.execute("DELETE FROM flavour_vocabulary")
    db.executemany("INSERT INTO flavour_vocabulary VALUES (?,?,?,?)", [
        (entry["tag"], entry["french"], entry["family"], entry["group"])
        for entry in snapshot["flavour_vocabulary"]])
    for row in rows:
        values = [json.dumps(row[column], ensure_ascii=False) if column == "attributes"
                  else row[column] for column in columns]
        db.execute(f"INSERT INTO wines ({','.join(columns)}) VALUES ({placeholders}) "
                   f"ON CONFLICT(wine_id) DO UPDATE SET {updates}", values)
        db.executemany("INSERT INTO flavours VALUES (?,?,?)", [
            (row["wine_id"], flavour["tag"], flavour["provenance"]) for flavour in row["flavours"]])
    db.execute(f"DELETE FROM wines WHERE wine_id NOT IN ({','.join('?' for _ in ids)})", ids)
    db.execute("INSERT OR REPLACE INTO catalog_metadata VALUES ('source_commit', ?)",
               (snapshot["source_commit"],))


def connect(read_only=False):
    if read_only:
        db = sqlite3.connect(DB_PATH.resolve().as_uri() + "?mode=ro", uri=True)
    else:
        db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
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
            existing_columns = {row["name"] for row in db.execute("PRAGMA table_info(wines)")}
            for column, kind in CATALOG_COLUMNS.items():
                if column not in existing_columns:
                    db.execute(f"ALTER TABLE wines ADD COLUMN {column} {kind}")
            db.execute("""CREATE TABLE IF NOT EXISTS flavour_vocabulary (
                tag TEXT PRIMARY KEY, french TEXT NOT NULL, family TEXT NOT NULL,
                flavour_group TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS flavours (
                wine_id TEXT NOT NULL REFERENCES wines(wine_id) ON DELETE CASCADE,
                tag TEXT NOT NULL REFERENCES flavour_vocabulary(tag),
                provenance TEXT NOT NULL CHECK(provenance IN ('stated','guess')),
                PRIMARY KEY (wine_id,tag,provenance))""")
            db.execute("CREATE INDEX IF NOT EXISTS ix_flavour_search ON flavours(tag,provenance,wine_id)")
            db.execute("CREATE TABLE IF NOT EXISTS catalog_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            if db.execute("SELECT COUNT(*) FROM wines").fetchone()[0] == 0:
                apply_catalog(db, load_catalog())
    finally:
        db.close()
