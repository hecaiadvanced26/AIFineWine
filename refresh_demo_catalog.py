"""Update the four demo items, keeping remaining stock and all existing orders."""
import json
import sqlite3
from datetime import datetime, timezone

from database import DATA_DIR, connect, initialize


def refresh_catalog():
    initialize()
    rows = json.loads((DATA_DIR / "demo_wines.json").read_text())
    backup_path = DATA_DIR / ("wines-before-refresh-" +
                             datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".db")
    db = connect()
    try:
        backup = sqlite3.connect(backup_path)
        try:
            db.backup(backup)
        finally:
            backup.close()
        with db:
            for row in rows:
                db.execute("""UPDATE wines SET name=?, price_cents=?, vintage=?, attributes=?
                    WHERE wine_id=?""", (row["name"], row["price_cents"], row["vintage"],
                    json.dumps(row["attributes"]), row["wine_id"]))
    finally:
        db.close()
    return backup_path


if __name__ == "__main__":
    print("Catalog updated; existing stock and orders kept. Backup:", refresh_catalog())
