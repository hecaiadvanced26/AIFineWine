"""Guided-advice tools. The model proposes a profile; this code filters and ranks.

Only catalog facts are returned: price, stock, type, origin, grapes, ratings, the shop's style
profile (sweetness, body, acidity, tannin, fruitiness), food pairings, and aroma tags with their
provenance. Profile values and pairings are demo profiles typical for grape and style, not
measurements of each bottle. Nothing here claims how a wine tastes beyond 'the taster wrote X'
or 'X is typical for the style'.
"""
import unicodedata

from database import connect

TYPES = ("red", "white", "rose", "sparkling", "any")  # no "dessert" colour: sweet wines are white or sparkling here
FAMILIES = ("Red-wine fruit", "White-wine fruit", "Floral", "Oak ageing", "Vegetal", "Mineral")
MAX_RESULTS = 3

# Coarse words the customer can ask for -> the 1-5 levels they cover.
SWEETNESS = {"dry": (1, 2), "off-dry": (3,), "sweet": (4, 5)}
BODY = {"light": (1, 2), "medium": (3,), "full": (4, 5)}
LEVEL = {"low": (1, 2), "medium": (3,), "high": (4, 5)}
STRUCTURE = {"sweetness": SWEETNESS, "body": BODY, "acidity": LEVEL, "tannin": LEVEL, "fruitiness": LEVEL}
DISPLAY_WORDS = {
    "sweetness": {"dry": "Dry", "off-dry": "Off-dry", "sweet": "Sweet"},
    "body": {"light": "Light-bodied", "medium": "Medium-bodied", "full": "Full-bodied"},
    "acidity": {"low": "Low acidity", "medium": "Medium acidity", "high": "High acidity"},
    "tannin": {"low": "Soft tannins", "medium": "Medium tannins", "high": "Firm tannins"},
    "fruitiness": {"low": "Subtle fruit", "medium": "Fruity", "high": "Very fruity"},
}
GRAPE_ALIASES = {
    "shiraz": "syrah", "garnacha": "grenache", "cannonau": "grenache", "monastrell": "mourvedre",
    "mataro": "mourvedre", "spatburgunder": "pinot noir", "pinot nero": "pinot noir", "blauburgunder": "pinot noir",
    "pinot grigio": "pinot gris", "grauburgunder": "pinot gris", "weissburgunder": "pinot blanc",
    "tinta roriz": "tempranillo", "aragonez": "tempranillo", "tinto fino": "tempranillo",
    "cot": "malbec", "cabernet": "cabernet sauvignon", "sauvignon": "sauvignon blanc",
    "xarel-lo": "xarel-lo", "carignane": "carignan", "carinena": "carignan", "gruner": "gruner veltliner",
    "alvarinho": "albarino",
}
COUNTRY_ALIASES = {"usa": "united states", "us": "united states", "america": "united states",
                   "uk": "england", "united kingdom": "england", "britain": "england", "great britain": "england"}


# Words customers use that are not food tags in the catalogue: expanded to the tags that exist.
FOOD_ALIASES = {"dessert": ["fruit dessert", "pastry"], "desserts": ["fruit dessert", "pastry"],
                "pudding": ["fruit dessert", "pastry"], "venison": ["game meat"], "game": ["game meat"]}


def fold(text):
    """Lower-case ASCII form: 'Châteauneuf' -> 'chateauneuf'."""
    return unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower().strip()


def level_word(table, value):
    """Coarse word (e.g. 'full') for a 1-5 level, or None when the wine has no such value."""
    if value is None:
        return None
    for word, levels in table.items():
        if value in levels:
            return word
    return None


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


WINE_COLUMNS = ("wine_id,name,price_cents,vintage,stock,wine_type,country,region,appellation,classification,"
                "winery,user_rating,community_avg_rating,user_review,sweetness,body,acidity,tannin,fruitiness")


def _profile(row):
    """The shop's style profile as {dimension: coarse word} plus display labels."""
    words = {key: level_word(table, row[key]) for key, table in STRUCTURE.items()}
    labels = [DISPLAY_WORDS[key][word] for key, word in words.items() if word]
    return words, labels


def _wine_dict(row, aromas, matched, missing, wishes_total, grapes, pairings):
    words, labels = _profile(row)
    return {
        "wine_id": row["wine_id"], "name": row["name"], "price_eur": row["price_cents"] / 100,
        "vintage": row["vintage"], "stock": row["stock"], "wine_type": row["wine_type"],
        "country": row["country"], "region": row["region"], "appellation": row["appellation"],
        "classification": row["classification"], "producer": row["winery"], "grapes": grapes,
        "taster_rating": row["user_rating"], "community_rating": row["community_avg_rating"],
        "taster_note": row["user_review"],
        "profile": words, "profile_labels": labels, "food_pairings": pairings,
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


def _grapes_by_wine(db):
    result = {}
    for row in db.execute("SELECT wine_id, grape FROM wine_grapes ORDER BY position"):
        result.setdefault(row["wine_id"], []).append(row["grape"])
    return result


def _pairings_by_wine(db):
    result = {}
    for row in db.execute("SELECT wine_id, food FROM wine_pairings ORDER BY food"):
        result.setdefault(row["wine_id"], []).append(row["food"])
    return result


def _canonical_grape(name):
    key = fold(name)
    return GRAPE_ALIASES.get(key, key)


def _structure_wishes(args):
    wishes = []
    for key, table in STRUCTURE.items():
        word = args.get(key)
        if word is None:
            continue
        if word not in table:
            raise ValueError(f"{key} must be one of {', '.join(table)} or null.")
        wishes.append((key, word))
    return wishes


def recommend_wines(wine_type, budget_min_eur, budget_max_eur, aroma_families, aromas, country,
                    include_style_guesses, sweetness=None, body=None, acidity=None, tannin=None,
                    fruitiness=None, grapes=None, foods=None, region=None, vintage=None):
    """Rank in-stock wines against a structured profile. Colour and budget are hard filters."""
    if wine_type not in TYPES:
        raise ValueError("wine_type must be one of " + ", ".join(TYPES))
    low, high = _number(budget_min_eur, "budget_min_eur"), _number(budget_max_eur, "budget_max_eur")
    if low is not None and high is not None and low > high:
        raise ValueError("budget_min_eur is above budget_max_eur.")
    if not isinstance(aroma_families, list) or not isinstance(aromas, list):
        raise ValueError("aroma_families and aromas must be lists.")
    grapes = [] if grapes is None else grapes
    foods = [] if foods is None else foods
    if not isinstance(grapes, list) or not isinstance(foods, list):
        raise ValueError("grapes and foods must be lists.")
    if not isinstance(include_style_guesses, bool):
        raise ValueError("include_style_guesses must be true or false.")
    if isinstance(foods, list):
        expanded = []
        for food in foods:
            for tag in FOOD_ALIASES.get(fold(food), [food]) if isinstance(food, str) else [food]:
                if tag not in expanded:
                    expanded.append(tag)
        foods = expanded
    if vintage is not None and (isinstance(vintage, bool) or not isinstance(vintage, int) or not 1900 <= vintage <= 2100):
        raise ValueError("vintage must be a year such as 2020, or null.")
    bad = [f for f in aroma_families if f not in FAMILIES]
    if bad:
        raise ValueError("Unknown aroma family: " + ", ".join(map(str, bad)))
    structure_wishes = _structure_wishes({"sweetness": sweetness, "body": body, "acidity": acidity,
                                          "tannin": tannin, "fruitiness": fruitiness})
    country = country.strip() if isinstance(country, str) and country.strip() else None
    region = region.strip() if isinstance(region, str) and region.strip() else None

    db = connect(read_only=True)
    try:
        vocabulary = {r["tag"]: r["family"] for r in db.execute("SELECT tag, family FROM flavour_vocabulary")}
        unknown = [t for t in aromas if t not in vocabulary]
        if unknown:
            raise ValueError("Unknown aroma tag: " + ", ".join(map(str, unknown)))
        known_foods = {r[0] for r in db.execute("SELECT DISTINCT food FROM wine_pairings")}
        unknown = [f for f in foods if f not in known_foods]
        if unknown:
            raise ValueError("Unknown food tag: " + ", ".join(map(str, unknown))
                             + ". Known: " + ", ".join(sorted(known_foods)))
        known_grapes = {fold(g): g for g in (r[0] for r in db.execute("SELECT DISTINCT grape FROM wine_grapes"))}
        wanted_grapes = []
        for grape in grapes:
            key = _canonical_grape(grape)
            if key not in known_grapes:
                raise ValueError(f"Unknown grape: {grape}. Known: " + ", ".join(sorted(known_grapes.values())))
            wanted_grapes.append(key)
        aroma_map = _aromas_by_wine(db)
        grape_map = _grapes_by_wine(db)
        pairing_map = _pairings_by_wine(db)
        rows = db.execute(f"SELECT {WINE_COLUMNS} FROM wines WHERE stock > 0").fetchall()
    finally:
        db.close()

    wishes = []
    if wine_type != "any":
        wishes.append(f"colour: {wine_type}")
    if low is not None or high is not None:
        wishes.append("budget")
    wishes += [f"aroma family: {f}" for f in aroma_families] + [f"aroma: {t}" for t in aromas]
    wishes += [f"{key}: {word}" for key, word in structure_wishes]
    wishes += [f"grape: {known_grapes[g]}" for g in wanted_grapes] + [f"food: {f}" for f in foods]
    if vintage:
        wishes.append(f"vintage: {vintage}")
    if region:
        wishes.append(f"region: {region}")
    if country:
        wishes.append(f"country: {country}")

    ranked = []
    guess_only_hits = 0
    place_hits = {"region": 0, "country": 0}
    for row in rows:
        price = row["price_cents"] / 100
        if wine_type != "any" and row["wine_type"] != wine_type:
            continue
        if (low is not None and price < low) or (high is not None and price > high):
            continue
        aromas_here = aroma_map.get(row["wine_id"], [])
        grapes_here = grape_map.get(row["wine_id"], [])
        pairings_here = pairing_map.get(row["wine_id"], [])
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
        for key, word in structure_wishes:
            if row[key] is not None and row[key] in STRUCTURE[key][word]:
                matched.append(f"{key}: {word}")
            else:
                missing.append(f"{key}: {word}")
        wine_grapes = {fold(g) for g in grapes_here}
        for key in wanted_grapes:
            (matched if key in wine_grapes else missing).append(f"grape: {known_grapes[key]}")
        for food in foods:
            (matched if food in pairings_here else missing).append(f"food: {food}")
        if vintage:
            (matched if row["vintage"] == vintage else missing).append(f"vintage: {vintage}")
        if region:
            wanted = fold(region)
            haystack = [fold(row["region"] or ""), fold(row["appellation"] or "")]
            if any(wanted == h or (len(wanted) > 3 and (wanted in h or h in wanted)) for h in haystack if h):
                matched.append(f"region: {region}")
                place_hits["region"] += 1
            else:
                missing.append(f"region: {region}")
        if country:
            wanted = COUNTRY_ALIASES.get(fold(country), fold(country))
            if fold(row["country"] or "") == wanted:
                matched.append(f"country: {row['country']}")
                place_hits["country"] += 1
            else:
                missing.append(f"country: {country}")
        stated_hits = sum("taster-stated" in m for m in matched)
        rating = row["user_rating"] if row["user_rating"] is not None else -1
        ranked.append((-len(matched), -stated_hits, -(row["community_avg_rating"] or 0), -rating, price,
                       row["wine_id"],
                       _wine_dict(row, aromas_here, matched, missing, len(wishes), grapes_here, pairings_here)))
    ranked.sort(key=lambda item: item[:6])
    wines = [item[6] for item in ranked[:MAX_RESULTS]]
    # A place nobody has is not a soft wish: showing other places' wines would answer a different question.
    absent = [f"{kind}: {value}" for kind, value in (("region", region), ("country", country))
              if value and ranked and not place_hits[kind]]
    if absent:
        return {"status": "no_matches", "wishes": wishes, "candidates_after_hard_filters": len(ranked), "wines": [],
                "note": "No in-stock wine matches " + " and ".join(absent) + ". Tell the customer plainly that "
                        "the shop has none, show no wines, and ask whether to search without that restriction."}
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
    """Cheaper in-stock wines of the same colour that share grapes or aroma tags with the chosen one."""
    db = connect(read_only=True)
    try:
        base = db.execute(f"SELECT {WINE_COLUMNS} FROM wines WHERE wine_id = ?", (wine_id,)).fetchone()
        if not base:
            return {"error": "Unknown wine ID."}
        aroma_map = _aromas_by_wine(db)
        grape_map = _grapes_by_wine(db)
        pairing_map = _pairings_by_wine(db)
        rows = db.execute(f"""SELECT {WINE_COLUMNS} FROM wines
                WHERE stock > 0 AND wine_type = ? AND price_cents < ? AND wine_id != ?""",
                          (base["wine_type"], base["price_cents"], wine_id)).fetchall()
    finally:
        db.close()
    base_tags = {t for t, _ in aroma_map.get(wine_id, [])}
    base_grapes = {fold(g) for g in grape_map.get(wine_id, [])}
    ranked = []
    for row in rows:
        here = aroma_map.get(row["wine_id"], [])
        shared = sorted(base_tags & {t for t, _ in here})
        shared_grapes = [g for g in grape_map.get(row["wine_id"], []) if fold(g) in base_grapes]
        if not shared and not shared_grapes:
            continue
        same_country = bool(base["country"]) and row["country"] == base["country"]
        distance = sum(abs(row[k] - base[k]) for k in ("sweetness", "body", "acidity", "tannin")
                       if row[k] is not None and base[k] is not None)
        rating = row["user_rating"] if row["user_rating"] is not None else -1
        reasons = ([f"shared grapes: {', '.join(shared_grapes)}"] if shared_grapes else []) \
            + ([f"shared aromas: {', '.join(shared)}"] if shared else []) + (["same country"] if same_country else [])
        ranked.append((-len(shared_grapes), distance, -len(shared), not same_country, -rating, row["price_cents"],
                       row["wine_id"],
                       _wine_dict(row, here, reasons, [], 1, grape_map.get(row["wine_id"], []),
                                  pairing_map.get(row["wine_id"], []))
                       | {"fit_score": None, "price_difference_eur": (base["price_cents"] - row["price_cents"]) / 100,
                          "shared_aromas": shared, "shared_grapes": shared_grapes}))
    ranked.sort(key=lambda item: item[:7])
    base_dict = _wine_dict(base, aroma_map.get(wine_id, []), [], [], 0, grape_map.get(wine_id, []),
                           pairing_map.get(wine_id, []))
    return {"status": "ok" if ranked else "no_matches", "chosen": base_dict,
            "alternatives": [item[7] for item in ranked[:2]],
            "note": ("Similarity here means same colour, lower price, shared grapes and/or shared aroma tags, "
                     "with the closest style profile first. It is not a tasting comparison.")}


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
