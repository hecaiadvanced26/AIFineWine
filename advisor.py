"""Guided-advice tools. The model proposes a profile; this code filters and ranks.

Only catalog facts are returned: price, stock, type, origin, ratings and aroma tags with
their provenance. Nothing here claims how a wine tastes beyond 'the taster wrote X' or
'X is typical for the style'.
"""
from database import connect

TYPES = ("red", "white", "rose", "sparkling", "dessert", "any")
FAMILIES = ("Red-wine fruit", "White-wine fruit", "Floral", "Oak ageing", "Vegetal", "Mineral")
MAX_RESULTS = 3


def _number(value, name):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{name} must be a non-negative number or null.")
    return float(value)


def fit_score(met, total):
    """1-5 glasses: the share of the customer's wishes this wine meets. None without wishes."""
    if total <= 0:
        return None
    return max(1, min(5, int(5 * met / total + 0.5)))


def _wine_dict(row, aromas, matched, missing, wishes_total):
    return {
        "wine_id": row["wine_id"], "name": row["name"], "price_eur": row["price_cents"] / 100,
        "vintage": row["vintage"], "stock": row["stock"], "wine_type": row["wine_type"],
        "country": row["country"], "region": row["region"],
        "taster_rating": row["user_rating"], "community_rating": row["community_avg_rating"],
        "aromas_stated": sorted(t for t, p in aromas if p == "stated"),
        "aromas_style_guess": sorted(t for t, p in aromas if p == "guess"),
        "wishes_met": len(matched), "wishes_total": wishes_total, "fit_score": fit_score(len(matched), wishes_total),
        "matched": matched, "not_matched": missing,
    }


def _aromas_by_wine(db):
    result = {}
    for row in db.execute("SELECT wine_id, tag, provenance FROM flavours"):
        result.setdefault(row["wine_id"], []).append((row["tag"], row["provenance"]))
    return result


def recommend_wines(wine_type, budget_min_eur, budget_max_eur, aroma_families, aromas,
                    country, include_style_guesses):
    """Rank in-stock wines against a structured profile. Colour and budget are hard filters."""
    if wine_type not in TYPES:
        raise ValueError("wine_type must be one of " + ", ".join(TYPES))
    low, high = _number(budget_min_eur, "budget_min_eur"), _number(budget_max_eur, "budget_max_eur")
    if low is not None and high is not None and low > high:
        raise ValueError("budget_min_eur is above budget_max_eur.")
    if not isinstance(aroma_families, list) or not isinstance(aromas, list):
        raise ValueError("aroma_families and aromas must be lists.")
    if not isinstance(include_style_guesses, bool):
        raise ValueError("include_style_guesses must be true or false.")
    bad = [f for f in aroma_families if f not in FAMILIES]
    if bad:
        raise ValueError("Unknown aroma family: " + ", ".join(map(str, bad)))
    country = country.strip() if isinstance(country, str) and country.strip() else None

    db = connect(read_only=True)
    try:
        vocabulary = {r["tag"]: r["family"] for r in db.execute("SELECT tag, family FROM flavour_vocabulary")}
        unknown = [t for t in aromas if t not in vocabulary]
        if unknown:
            raise ValueError("Unknown aroma tag: " + ", ".join(map(str, unknown)))
        aroma_map = _aromas_by_wine(db)
        rows = db.execute("""SELECT wine_id,name,price_cents,vintage,stock,wine_type,country,region,
                user_rating,community_avg_rating FROM wines WHERE stock > 0""").fetchall()
    finally:
        db.close()

    wishes = []
    if wine_type != "any":
        wishes.append(f"colour: {wine_type}")
    if low is not None or high is not None:
        wishes.append("budget")
    wishes += [f"aroma family: {f}" for f in aroma_families] + [f"aroma: {t}" for t in aromas]
    if country:
        wishes.append(f"country: {country}")

    ranked = []
    guess_only_hits = 0
    for row in rows:
        price = row["price_cents"] / 100
        if wine_type != "any" and row["wine_type"] != wine_type:
            continue
        if (low is not None and price < low) or (high is not None and price > high):
            continue
        aromas_here = aroma_map.get(row["wine_id"], [])
        usable = [(t, p) for t, p in aromas_here if p == "stated" or include_style_guesses]
        matched, missing = [], []
        if wine_type != "any":
            matched.append(f"colour: {wine_type}")
        if low is not None or high is not None:
            matched.append("budget")
        for family in aroma_families:
            hit = [(t, p) for t, p in usable if vocabulary[t] == family]
            if hit:
                kind = "taster-stated" if any(p == "stated" for _, p in hit) else "style guess"
                matched.append(f"aroma family: {family} ({kind})")
            else:
                missing.append(f"aroma family: {family}")
                if any(vocabulary[t] == family for t, _ in aromas_here):
                    guess_only_hits += 1
        for tag in aromas:
            hit = [p for t, p in usable if t == tag]
            if hit:
                matched.append(f"aroma: {tag} ({'taster-stated' if 'stated' in hit else 'style guess'})")
            else:
                missing.append(f"aroma: {tag}")
        if country:
            if (row["country"] or "").lower() == country.lower():
                matched.append(f"country: {row['country']}")
            else:
                missing.append(f"country: {country}")
        stated_hits = sum("taster-stated" in m for m in matched)
        rating = row["user_rating"] if row["user_rating"] is not None else -1
        ranked.append((-len(matched), -stated_hits, -rating, price, row["wine_id"],
                       _wine_dict(row, aromas_here, matched, missing, len(wishes))))
    ranked.sort(key=lambda item: item[:5])
    wines = [item[5] for item in ranked[:MAX_RESULTS]]
    # Soft wishes that nobody satisfied: tell the model rather than letting it pretend.
    result = {"status": "ok" if wines else "no_matches", "wishes": wishes,
              "candidates_after_hard_filters": len(ranked), "wines": wines}
    if not wines:
        result["note"] = "No in-stock wine fits colour and budget. Ask before changing them."
    elif any(w["not_matched"] for w in wines):
        result["note"] = ("Some wishes are not met by every wine; say which. Cards show them to "
                          "the customer.")
    if not include_style_guesses and (aroma_families or aromas) and (
            guess_only_hits or any(w["not_matched"] for w in wines)):
        result["style_guess_hint"] = ("Wines without taster-stated aromas were not counted. Ask the "
                                      "customer before re-running with include_style_guesses=true.")
    return result


def find_cheaper_alternatives(wine_id):
    """Cheaper in-stock wines of the same colour that share aroma tags with the chosen one."""
    db = connect(read_only=True)
    try:
        base = db.execute("""SELECT wine_id,name,price_cents,vintage,stock,wine_type,country,region,
                user_rating,community_avg_rating FROM wines WHERE wine_id = ?""", (wine_id,)).fetchone()
        if not base:
            return {"error": "Unknown wine ID."}
        aroma_map = _aromas_by_wine(db)
        rows = db.execute("""SELECT wine_id,name,price_cents,vintage,stock,wine_type,country,region,
                user_rating,community_avg_rating FROM wines
                WHERE stock > 0 AND wine_type = ? AND price_cents < ? AND wine_id != ?""",
                          (base["wine_type"], base["price_cents"], wine_id)).fetchall()
    finally:
        db.close()
    base_tags = {t for t, _ in aroma_map.get(wine_id, [])}
    ranked = []
    for row in rows:
        here = aroma_map.get(row["wine_id"], [])
        shared = sorted(base_tags & {t for t, _ in here})
        if not shared:
            continue
        same_country = bool(base["country"]) and row["country"] == base["country"]
        rating = row["user_rating"] if row["user_rating"] is not None else -1
        ranked.append((-len(shared), not same_country, -rating, row["price_cents"], row["wine_id"],
                       _wine_dict(row, here, [f"shared aromas: {', '.join(shared)}"]
                                  + (["same country"] if same_country else []), [], 1)
                       | {"fit_score": None, "price_difference_eur": (base["price_cents"] - row["price_cents"]) / 100,
                          "shared_aromas": shared}))
    ranked.sort(key=lambda item: item[:5])
    base_dict = _wine_dict(base, aroma_map.get(wine_id, []), [], [], 0)
    return {"status": "ok" if ranked else "no_matches", "chosen": base_dict,
            "alternatives": [item[5] for item in ranked[:2]],
            "note": ("Similarity here means shared aroma tags (taster-stated or style-typical), "
                     "same colour, lower price. It is not a tasting comparison.")}


def offer_choices(options, step, total):
    """Quick-reply buttons for the customer. The question itself goes in the written reply."""
    if not isinstance(options, list) or not 2 <= len(options) <= 6 or not all(
            isinstance(o, str) and 0 < len(o.strip()) <= 60 for o in options):
        raise ValueError("options must be 2-6 short strings.")
    for value, name in ((step, "step"), (total, "total")):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > 10:
            raise ValueError(f"{name} must be an integer from 1 to 10.")
    if step > total:
        raise ValueError("step is above total.")
    return {"status": "shown", "options": [o.strip() for o in options], "step": step, "total": total,
            "next": "Now write ONE short question in your reply. Do not repeat the options."}
