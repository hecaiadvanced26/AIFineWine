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


def run_query(sql):
    if not isinstance(sql, str) or not sql.strip().upper().startswith("SELECT"):
        return {"status": "query_error", "error": "Provide one SELECT query."}
    db = connect(read_only=True)
    try:
        rows = [dict(row) for row in db.execute(sql).fetchmany(10)]
        return {"status": "ok" if rows else "no_matches", "rows": rows}
    except sqlite3.Error as error:
        return {"status": "query_error", "error": str(error)}
    finally:
        db.close()
