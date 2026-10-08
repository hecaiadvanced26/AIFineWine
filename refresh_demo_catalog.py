"""Import the bundled catalog with a backup, keeping stock for retained IDs and orders."""
import sqlite3
from datetime import datetime, timezone

from database import DATA_DIR, apply_catalog, connect, initialize, load_catalog


def refresh_catalog():
    snapshot = load_catalog()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = DATA_DIR / ("wines-before-refresh-" +
                             datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".db")
    db = connect()
    try:
        backup = sqlite3.connect(backup_path)
        try:
            db.backup(backup)
        finally:
            backup.close()
    finally:
        db.close()
    initialize()
    db = connect()
    try:
        with db:
            apply_catalog(db, snapshot)
    finally:
        db.close()
    return backup_path


if __name__ == "__main__":
    print("Catalog updated; existing stock and orders kept. Backup:", refresh_catalog())
