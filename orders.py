"""Prepare one-item orders and export confirmed demo orders locally."""
import json
from datetime import datetime, timezone
from uuid import uuid4

from catalog import get_wine_details
from database import DATA_DIR, connect


def prepare_order(wine_id, quantity):
    wine = get_wine_details(wine_id)
    if "error" in wine:
        return wine
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        return {"error": "Quantity must be a positive integer."}
    if quantity > wine["stock"]:
        return {"error": "Not enough stock for this quantity."}
    return {"order_id": str(uuid4()), "status": "awaiting_confirmation",
            "wine_id": wine_id, "name": wine["name"], "vintage": wine["vintage"],
            "quantity": quantity, "unit_price_cents": round(wine["price_eur"] * 100),
            "total_cents": round(wine["price_eur"] * 100) * quantity,
            "currency": "EUR"}


def submit_order(draft):
    """Called by the UI/CLI only after explicit confirmation; not a model tool."""
    db = connect()
    try:
        with db:
            existing = db.execute("SELECT payload FROM orders WHERE order_id = ?",
                                  (draft["order_id"],)).fetchone()
            if existing:
                order = json.loads(existing["payload"])
            else:
                changed = db.execute("""UPDATE wines SET stock = stock - ?
                    WHERE wine_id = ? AND stock >= ? AND price_cents = ?
                    AND vintage IS ?""", (draft["quantity"], draft["wine_id"],
                    draft["quantity"], draft["unit_price_cents"], draft["vintage"]))
                if changed.rowcount != 1:
                    return {"error": "Price, vintage or stock changed. Prepare a new order."}
                order = {**draft, "status": "exported_locally",
                         "created_at": datetime.now(timezone.utc).isoformat()}
                db.execute("INSERT INTO orders VALUES (?, ?)",
                           (order["order_id"], json.dumps(order)))
    finally:
        db.close()
    # If writing the file fails, retrying the same ID will not reduce stock twice.
    folder = DATA_DIR / "orders"
    folder.mkdir(exist_ok=True)
    path = folder / (order["order_id"] + ".json")
    path.write_text(json.dumps(order, indent=2), encoding="utf-8")
    return {"status": "exported_locally", "order_id": order["order_id"],
            "file": str(path), "note": "Demo export only; not sent to a shop."}
