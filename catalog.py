"""Execute the model's SQL against the catalog."""
import json
import sqlite3

from database import connect


def wine_record(row):
    wine = dict(row)
    wine["price_eur"] = wine.pop("price_cents") / 100
    wine["attributes"] = json.loads(wine["attributes"])
    return wine


def get_wine_details(wine_id):
    db = connect(read_only=True)
    try:
        row = db.execute("SELECT * FROM wines WHERE wine_id = ?", (wine_id,)).fetchone()
        if row is None:
            return {"error": "Unknown wine ID."}
        wine = wine_record(row)
        wine["flavours"] = [dict(flavour) for flavour in db.execute(
            "SELECT tag,provenance FROM flavours WHERE wine_id=? ORDER BY provenance,tag", (wine_id,))]
        return wine
    finally:
        db.close()


QUERYABLE_TABLES = {"wines", "flavours", "flavour_vocabulary", "wine_grapes", "wine_pairings"}
HIDDEN_COLUMNS = {"stock", "inventory_synthetic"}  # internal: never returned to the model
MAX_VM_STEPS = 3_000_000  # aborts runaway joins (about a second of work)


def _authorize(action, arg1, arg2, database, source):
    """Only SELECT on the customer-facing tables; no orders, metadata, sqlite_master, PRAGMA or ATTACH."""
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ:
        return sqlite3.SQLITE_OK if arg1 in QUERYABLE_TABLES else sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION:
        return sqlite3.SQLITE_DENY if str(arg2).lower() in ("load_extension", "readfile", "writefile") else sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def run_query(sql):
    if not isinstance(sql, str) or not sql.strip().upper().startswith("SELECT"):
        return {"status": "query_error", "error": "Provide one SELECT query."}
    db = connect(read_only=True)
    db.set_authorizer(_authorize)
    steps = [0]

    def budget():
        steps[0] += 1
        return 1 if steps[0] > MAX_VM_STEPS // 1000 else 0
    db.set_progress_handler(budget, 1000)
    try:
        rows = [{key: value for key, value in dict(row).items() if key not in HIDDEN_COLUMNS}
                for row in db.execute(sql).fetchmany(10)]
        return {"status": "ok" if rows else "no_matches", "rows": rows}
    except sqlite3.Error as error:
        return {"status": "query_error", "error": str(error)}
    finally:
        db.close()
