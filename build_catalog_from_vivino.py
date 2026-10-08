"""Build data/demo_wines.json (this app's catalog format) from the team's taster data.

Inputs (in data/source/):
  wines.json              - cleaned Vivino export: real wines, vintage, taster rating, aroma tags (free-text reviews removed from this copy) (prepare_data.py + add_flavours.py)
  shop_inventory.json     - INVENTED price, stock and bottle size per wine (add_shop_layer.py)
  flavour_vocabulary.json - the 88 aroma tags (English) of the aroma wheel
Outputs: data/demo_wines.json and data/source/wine_id_map.json (W-001... -> source id)

Usage: python build_catalog_from_vivino.py 
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "data" / "source"
TYPE_MAP = {"Red Wine": "red", "White Wine": "white", "Rosé Wine": "rose",
            "Sparkling": "sparkling", "Dessert Wine": "dessert"}   # "Unknown" -> no type
COUNTRY_FIX = {"fr": "France", "de": "Germany"}                    # ISO-2 codes found in the export


def load(name):
    return json.loads((SRC / name).read_text(encoding="utf-8"))


def build(include_comments=False):  # comments are not part of this repo
    wines = load("wines.json")
    inventory = load("shop_inventory.json")["inventory"]
    vocab = {v["tag"] for v in load("flavour_vocabulary.json")}
    rows, id_map = [], {}
    for number, w in enumerate(sorted(wines, key=lambda x: x["id"]), start=1):
        wine_id = f"W-{number:03d}"
        shop = inventory[w["id"]]
        tags = w["flavours_stated"] + w["flavours_inferred"]
        assert set(tags) <= vocab, (w["id"], set(tags) - vocab)
        attrs = {"brand": w["winery"], "type": TYPE_MAP.get(w["wine_type"]),
                 "country": COUNTRY_FIX.get(w["country"], w["country"]),
                 "region": w["region"], "style": w["regional_style"],
                 "taste": w["flavours_stated"], "taste_style_guess": w["flavours_inferred"],
                 "taster_rating": w["user_rating"], "community_rating": w["community_avg_rating"],
                 "bottle_ml": shop["bottle_ml"], "shop_data": "invented demo data"}
        if include_comments and w.get("user_review"):
            attrs["taster_comment"] = w["user_review"]
        rows.append({"wine_id": wine_id, "name": (f"{w['winery']} {w['wine_name']}" if w["winery"] else w["wine_name"]),
                     "price_cents": round(shop["price_eur"] * 100), "vintage": w["vintage"],
                     "stock": shop["stock"], "attributes": attrs})
        id_map[wine_id] = w["id"]
    return rows, id_map


if __name__ == "__main__":
    rows, id_map = build()
    (HERE / "data" / "demo_wines.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (SRC / "wine_id_map.json").write_text(json.dumps(id_map, indent=1) + "\n", encoding="utf-8")
    print(f"{len(rows)} wines written to data/demo_wines.json")
