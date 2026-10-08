"""Export a reproducible, validated catalog snapshot from the finewine repository."""
import argparse
import json
import sqlite3
import subprocess
from decimal import Decimal
from pathlib import Path

SOURCE_URL = "https://github.com/hecaiadvanced26/finewine"
TYPES = {"Red Wine": "red", "White Wine": "white", "Rosé Wine": "rose",
         "Sparkling": "sparkling", "Dessert Wine": "dessert", "Unknown": "unknown"}


def export_catalog(source: Path | str, destination: Path | str) -> int:
    source, destination = Path(source), Path(destination)
    vocabulary = json.loads((source / "flavour_vocabulary.json").read_text(encoding="utf-8"))
    tags = {entry["tag"] for entry in vocabulary}
    db = sqlite3.connect((source / "wine_shop.sqlite").resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        wines = []
        for row in db.execute("""SELECT w.*, i.price_eur, i.stock, i.bottle_ml, i.synthetic
                FROM wines w JOIN inventory i ON i.wine_id=w.id ORDER BY w.id"""):
            cents = Decimal(str(row["price_eur"])) * 100
            if cents != cents.to_integral_value() or cents < 0 or row["stock"] < 0:
                raise ValueError(f"Invalid inventory for {row['id']}")
            flavours = [dict(flavour) for flavour in db.execute(
                "SELECT tag, provenance FROM flavours WHERE wine_id=? ORDER BY provenance,tag",
                (row["id"],))]
            if any(f["tag"] not in tags or f["provenance"] not in {"stated", "guess"} for f in flavours):
                raise ValueError(f"Invalid flavour provenance for {row['id']}")
            country = {"de": "Germany", "fr": "France"}.get(row["country"], row["country"])
            wine_type = TYPES[row["wine_type"]]
            wines.append({"wine_id": row["id"],
                "name": " ".join(filter(None, [row["winery"], row["wine_name"]])),
                "price_cents": int(cents), "stock": row["stock"], "vintage": row["vintage"],
                "winery": row["winery"], "country": country, "region": row["region"],
                "regional_style": row["regional_style"], "wine_type": wine_type,
                "user_rating": row["user_rating"], "community_avg_rating": row["community_avg_rating"],
                "user_review": row["user_review"], "bottle_ml": row["bottle_ml"],
                "inventory_synthetic": row["synthetic"], "flavours": flavours,
                "attributes": {"brand": row["winery"], "type": wine_type,
                    "country": country, "country_original": row["country"], "region": row["region"],
                    "source_url": SOURCE_URL,
                    "flavours_stated": [f["tag"] for f in flavours if f["provenance"] == "stated"],
                    "flavours_inferred": [f["tag"] for f in flavours if f["provenance"] == "guess"]}})
        if len(wines) != db.execute("SELECT COUNT(*) FROM wines").fetchone()[0]:
            raise ValueError("Some wines are missing inventory")
        if not wines:
            raise ValueError("Source catalog is empty")
    finally:
        db.close()
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    snapshot = {"source_url": SOURCE_URL, "source_commit": revision,
                "inventory_note": "Prices, stock and bottle sizes are fictional seeded shop data.",
                "ratings_note": "Imported taster and community scores; not independently verified.",
                "wines": wines, "flavour_vocabulary": vocabulary}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(wines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "data" / "catalog.json")
    args = parser.parse_args()
    print("Exported wines:", export_catalog(args.source, args.output))
