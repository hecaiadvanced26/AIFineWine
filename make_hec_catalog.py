"""Build the fictional cave. catalogue: python make_hec_catalog.py

Writes data/catalog.json (250 wines). Deterministic: the same script gives the same file.
Real: country, region, appellation, grape varieties (see hec_catalog_data.py for sources).
Invented: producers, cuvee names, vintages, prices, stock, ratings, the 75 tasting notes.
Tasting notes live in data/tasting_notes.json (written by hand, checked here).

  python make_hec_catalog.py              build the catalogue
  python make_hec_catalog.py --selection  print the 75 wines that receive a tasting note
"""
import csv
import json
import random
import re
import sys
import unicodedata
from pathlib import Path

from hec_catalog_data import FOODS, G, TEMPLATES, TIER_PRICE_EUR

ROOT = Path(__file__).parent
SEED = 20261009
N_NOTES = 75

# Display spelling (the data tables use plain ASCII so they are easy to type and diff).
DISPLAY = {
    "Cote-Rotie": "Côte-Rôtie", "Chateauneuf-du-Pape": "Châteauneuf-du-Pape", "Saint-Estephe": "Saint-Estèphe",
    "Saint-Emilion Grand Cru": "Saint-Émilion Grand Cru", "Haut-Medoc": "Haut-Médoc",
    "Pessac-Leognan": "Pessac-Léognan", "Pouilly-Fuisse": "Pouilly-Fuissé", "Pouilly-Fume": "Pouilly-Fumé",
    "Savennieres": "Savennières", "Muscadet Sevre-et-Maine": "Muscadet Sèvre-et-Maine",
    "Macon-Villages": "Mâcon-Villages", "Bordeaux Superieur": "Bordeaux Supérieur", "Bordeaux Blanc": "Bordeaux Blanc",
    "Cotes du Rhone": "Côtes du Rhône", "Cotes de Provence": "Côtes de Provence", "Faugeres": "Faugères",
    "Corbieres": "Corbières", "Rias Baixas": "Rías Baixas", "Dao": "Dão", "Niederosterreich": "Niederösterreich",
    "Rhone Valley": "Rhône Valley", "Castilla y Leon": "Castilla y León", "Cremant d'Alsace": "Crémant d'Alsace",
    "Cremant de Loire": "Crémant de Loire", "Cremant de Bourgogne": "Crémant de Bourgogne",
    "Cremant de Limoux": "Crémant de Limoux", "Spatlese": "Spätlese", "Millesime": "Millésimé", "Rose": "Rosé",
    "Apremont": "Apremont", "Coteaux d'Aix-en-Provence": "Coteaux d'Aix-en-Provence", "Hawke's Bay": "Hawke's Bay",
    "Jacquere": "Jacquère", "Albarino": "Albariño", "Gruner Veltliner": "Grüner Veltliner",
    "Blaufrankisch": "Blaufränkisch", "Carmenere": "Carménère", "Mourvedre": "Mourvèdre", "Semillon": "Sémillon",
    "Torrontes": "Torrontés", "Mencia": "Mencía", "Gewurztraminer": "Gewürztraminer",
    "Alsace Gewurztraminer": "Alsace Gewurztraminer", "Alto Adige Gewurztraminer": "Alto Adige Gewürztraminer",
    "Savennieres ": "Savennières",
}


def disp(text):
    return DISPLAY.get(text, text)


def fold(text):
    """Lower-case ASCII version for search_text."""
    return unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower()


# --- invented producer names -----------------------------------------------------------------
FR_A = ["Aub", "Bel", "Cant", "Dorv", "Estr", "Font", "Gaum", "Haut", "Jourd", "Lauv", "Malv", "Orm", "Pern",
        "Quer", "Rouv", "Sauv", "Tarv", "Vauc", "Verm", "Mont", "Sarr", "Cler", "Brun", "Valm", "Roch", "Lanc"]
FR_B = ["elle", "aval", "ereau", "ignac", "ouze", "ières", "eval", "aie", "ancourt", "oray", "ellac", "ardent",
        "onne", "ières", "ault", "ouvre"]
FR_PL = ["Hautes-Roches", "Quatre Vents", "Trois Chênes", "Aubépines", "Grands Champs", "Pierres Blanches",
         "Terrasses", "Cèdres", "Fontaines", "Ormeaux", "Genêts", "Rouvières", "Tourelles", "Combes", "Coteaux Dorés"]
IT_A = ["Mon", "Val", "Rocca", "Sasso", "Campo", "Casa", "Pian", "Colle", "Bosco", "Fonte", "Villa", "Poggio"]
IT_B = ["alto", "bruno", "chiaro", "verde", "dorato", "rosso", "lungo", "nuovo", "scuro", "fiorito", "bello", "sereno"]
ES_A = ["Sierra", "Vega", "Peña", "Cerro", "Monte", "Valle", "Rio", "Casa", "Fuente", "Cumbre"]
ES_B = ["Clara", "Dorada", "Brava", "Alta", "Roja", "Serena", "Larga", "Nueva", "Antigua", "Verde"]
PT_A = ["Vale", "Monte", "Rio", "Pedra", "Serra", "Cabeço", "Lagar", "Sobreiro"]
PT_B = ["Sereno", "Alto", "Fundo", "Longa", "Branca", "Velho", "Grande", "Novo"]
DE_A = ["Stein", "Berg", "Rhein", "Mosel", "Hang", "Sonnen", "Kalk", "Fels", "Reben", "Linden"]
DE_B = ["hof", "berg", "halde", "gut", "tal", "bach", "lay", "stein", "garten"]
EN_A = ["Larkspur", "Ridgeline", "Foxglove", "Bluestem", "Copper", "Silver", "Willow", "Cobble", "Meadow",
        "Granite", "Juniper", "Harbor", "Thistle", "Alder", "Sagebrush"]
EN_B = ["Hill", "Creek", "Ranch", "Flat", "Terrace", "Bench", "Run", "Peak", "Crossing", "Spring", "Ridge", "Fork"]
CUVEES = {
    "France": ["Les Terrasses", "Vieilles Vignes", "Cuvée Prestige", "La Source", "Clos du Moulin", "Les Grands Champs",
               "Cuvée Tradition", "L'Ancienne", "Les Hauts Plans", "Cuvée Charlotte", "Terroir d'Argile", "Les Silex"],
    "Italy": ["Vigna Alta", "Colle Lungo", "Podere Vecchio", "La Quercia", "Bricco Rosso", "Campo Grande", "Le Rose",
              "Vigna del Nonno"],
    "Spain": ["Finca Vieja", "Tierra Alta", "La Solana", "Viñedo del Cerro", "Cepas Viejas", "La Umbría"],
    "Portugal": ["Vinha Velha", "Lote 7", "Vinhas do Rio", "Talhão Alto"],
    "Germany": ["Alte Reben", "Terrassen", "Steillage", "Hausmarke", "Lage Sonnenhang"],
    "Austria": ["Alte Reben", "Terrassen", "Hausmarke"],
    "default": ["Old Vine", "Hillside Block", "Block 12", "Home Ranch", "Single Vineyard", "Estate Selection",
                "Heritage", "Ridge Selection"],
}
CHAMPAGNE_CUVEES = ["Cuvée Tradition", "Brut Réserve", "Cuvée Prestige", "Grande Cuvée", "Cuvée des Fondateurs"]


def de(base):
    return ("d'" if base[0] in "AEIOUÉ" else "de ") + base


def producer_name(rng, country, region, colour, taken):
    for _ in range(200):
        if country == "France":
            if region == "Champagne":
                base = rng.choice(FR_A) + rng.choice(FR_B)
                name = f"Maison {base}" if rng.random() < .6 else f"{base} & Fils"
            elif region == "Bordeaux":
                base = rng.choice(FR_A) + rng.choice(FR_B)
                name = f"Château {base}" if rng.random() < .8 else f"Domaine {de(base)}"
            elif region == "Burgundy":
                name = f"Domaine {rng.choice(FR_A)}{rng.choice(FR_B)}-{rng.choice(FR_A)}{rng.choice(FR_B)}"
            else:
                r = rng.random()
                base = rng.choice(FR_A) + rng.choice(FR_B)
                name = (f"Domaine {de(base)}" if r < .35 else f"Domaine des {rng.choice(FR_PL)}" if r < .6
                        else f"Château {base}" if r < .8 else f"Maison {base}")
        elif country == "Italy":
            base = rng.choice(IT_A) + rng.choice(IT_B)
            word = "Cascina" if region == "Piedmont" and rng.random() < .5 else rng.choice(
                ["Tenuta", "Cantina", "Poderi", "Fattoria", "Azienda Agricola"])
            name = f"{word} {base.capitalize()}"
        elif country == "Spain":
            word = rng.choice(["Bodegas", "Finca", "Viña", "Bodega"])
            name = f"{word} {rng.choice(ES_A)} {rng.choice(ES_B)}"
        elif country == "Portugal":
            name = f"Quinta {rng.choice(['do', 'da', 'de'])} {rng.choice(PT_A)} {rng.choice(PT_B)}"
        elif country in ("Germany", "Austria"):
            name = f"Weingut {rng.choice(DE_A)}{rng.choice(DE_B)}"
        elif country == "Chile":
            name = f"Viña {rng.choice(ES_A)} {rng.choice(ES_B)}"
        elif country in ("Argentina", "Uruguay"):
            name = f"Bodega {rng.choice(ES_A)} {rng.choice(ES_B)}"
        elif country == "Greece":
            name = f"Domaine {rng.choice(IT_A)}{rng.choice(IT_B)}".replace("Domaine Mon", "Domaine Mono")
        elif country in ("Australia", "New Zealand", "England", "South Africa"):
            name = f"{rng.choice(EN_A)} {rng.choice(EN_B)} " + rng.choice(["Estate", "Wines", "Vineyard"])
        else:
            name = f"{rng.choice(EN_A)} {rng.choice(EN_B)} " + rng.choice(["Cellars", "Vineyards", "Wine Co."])
        if name.split()[0] == name.split()[1]:
            continue
        if name not in taken:
            taken.add(name)
            return name
    raise RuntimeError("could not invent a unique producer name")


# --- numeric helpers --------------------------------------------------------------------------
def clip(x, lo=1, hi=5):
    return max(lo, min(hi, x))


def blend(grapes, key):
    """Weighted blend of the grape ranges: first grape 60 %, the rest share 40 %."""
    weights = [1.0] if len(grapes) == 1 else [0.6] + [0.4 / (len(grapes) - 1)] * (len(grapes) - 1)
    lo = sum(w * G[g][key][0] for w, g in zip(weights, grapes))
    hi = sum(w * G[g][key][1] for w, g in zip(weights, grapes))
    return int(round(lo)), int(round(hi))


def round_price(eur, rng):
    if eur < 15:
        price = round(eur * 2) / 2
        if rng.random() < .5 and price > 6:
            price -= 0.10
    elif eur < 60:
        price = round(eur * 2) / 2
        if rng.random() < .3:
            price -= 0.10
    elif eur < 200:
        price = round(eur)
    else:
        price = round(eur / 5) * 5
    return int(round(price * 100))


def pick_level(rng, lo, hi):
    lo, hi = clip(lo), clip(hi)
    if lo > hi:
        lo = hi
    return rng.randint(lo, hi)


def structure(rng, t, cls_mods):
    """Sweetness, body, acidity, tannin, fruitiness for one bottle."""
    grapes = t.grapes
    body = t.body or tuple(clip(v + t.shift) for v in blend(grapes, "body"))
    acid = t.acid or tuple(clip(max(min(v, 2), v - t.shift)) for v in blend(grapes, "acid"))
    fruit = t.fruit or blend(grapes, "fruit")
    sweet = cls_mods.get("sweet", t.sweet)
    tannin = None
    if t.colour == "red":
        tannin = t.tannin or blend(grapes, "tannin")
    b_add, a_add, t_add = cls_mods.get("body_add", 0), cls_mods.get("acid_add", 0), cls_mods.get("tannin_add", 0)
    out = {
        "sweetness": pick_level(rng, *sweet),
        "body": pick_level(rng, body[0] + b_add, body[1] + b_add),
        "acidity": pick_level(rng, acid[0] + a_add, acid[1] + a_add),
        "tannin": None if tannin is None else pick_level(rng, tannin[0] + t_add, tannin[1] + t_add),
        "fruitiness": pick_level(rng, *fruit),
    }
    return out


def aroma_guesses(rng, t, premium):
    pool = []
    for i, g in enumerate(t.grapes):
        pool += [(a, 3 - min(i, 2)) for a in G[g]["aromas"]]
    seen, out = set(), []
    weighted = [a for a, w in pool for _ in range(w)]
    rng.shuffle(weighted)
    for a in weighted:
        if a not in seen:
            seen.add(a)
            out.append(a)
        if len(out) == 4:
            break
    return sorted(out)


def foods_for(rng, t, extra):
    pool = list(extra) if extra else []
    if not pool:
        for g in t.grapes:
            for f in G[g]["foods"]:
                if f not in pool:
                    pool.append(f)
    core, rest = pool[:3], pool[3:]
    rng.shuffle(rest)
    chosen = core + rest[:rng.randint(1, 2)]
    return sorted(set(chosen))


def build():
    rng = random.Random(SEED)
    taken = set()
    wines = []

    def make_one(t, producer, cuvee, cls, year, rating_offset=0.0, price_factor=1.0, u=None, same_as=None):
        label, mult, _, mods = cls
        mods = dict(mods)
        profile = structure(rng, t, mods) if same_as is None else {k: same_as[k] for k in (
            "sweetness", "body", "acidity", "tannin", "fruitiness")}
        lo, hi = TIER_PRICE_EUR[t.tier]
        price = lo * (hi / lo) ** (rng.random() if u is None else u) * mult * price_factor
        if t.colour == "red" and t.tier >= 3 and year:
            price *= 1 + 0.03 * max(0, 2024 - year - 3)
        base_rating = {1: 3.45, 2: 3.6, 3: 3.8, 4: 4.0, 5: 4.2}[t.tier]
        community = round(clip(base_rating + rng.gauss(0, .18) + rating_offset, 3.0, 4.7, ), 1)
        r = rng.random()
        stock = 0 if r < .1 else rng.randint(1, 4) if r < .3 else rng.randint(5, 20 if t.tier >= 4 else 40)
        style = t.style
        classification = label if label not in ("Millesime",) else "Millesime"
        if t.colour == "sparkling" and style and not classification:
            classification = style
        grapes = [disp(g) for g in t.grapes]
        # name
        if t.colour == "sparkling" and style:
            name = f"{producer} {disp(style)}"
        elif t.colour == "sparkling" and t.region == "Champagne":
            name = f"{producer} {rng.choice(CHAMPAGNE_CUVEES)}"
        else:
            name = f"{producer} {cuvee}" if cuvee else producer
        appellation = disp(t.appellation)
        regional_style = appellation + (f" {disp(classification)}" if classification and classification not in (
            "Brut", "Brut Nature", "Extra Brut", "Extra Dry", "Kabinett", "Spatlese", "Trocken", "Sec", "Demi-Sec",
            "Moelleux", "Crianza", "Reserva", "Gran Reserva", "Brut Nature Reserva", "Superiore DOCG", "Riserva",
            "Gran Selezione", "Millesime") else "")
        wine_year = None if (t.nv and mods.get("nv", t.nv)) else year
        if t.colour == "sparkling" and classification == "Millesime":
            wine_year = year
        wines.append(dict(
            name=name, winery=producer, country=t.country, region=disp(t.region), appellation=appellation,
            classification=(disp(classification) if classification else None), regional_style=regional_style,
            wine_type=t.colour, vintage=wine_year, price_cents=round_price(price, rng), stock=stock,
            community_avg_rating=community, grapes=grapes, bottle_ml=mods.get("ml", t.ml), **profile,
            pairings=(foods_for(rng, t, mods.get("foods") or t.foods) if same_as is None else list(same_as["pairings"])),
            guesses=(aroma_guesses(rng, t, False) if same_as is None else list(same_as["guesses"])), _tier=t.tier,
        ))

    for t in TEMPLATES:
        for g in t.grapes:
            assert g in G, f"unknown grape {g}"
        classes = t.classes or [C0]
        weights = [c[2] for c in classes]
        triplets_done = 0
        singles = t.n - 3 * t.triplets
        assert singles >= 0, f"{t.appellation}: n too small for triplets"
        cuvee_pool = CUVEES.get(t.country, CUVEES["default"])
        for _ in range(singles):
            cls = rng.choices(classes, weights)[0]
            producer = producer_name(rng, t.country, t.region, t.colour, taken)
            cuvee = None if rng.random() < .4 else rng.choice(cuvee_pool)
            vint = cls[3].get("vint", t.vint)
            year = rng.randint(*vint)
            make_one(t, producer, cuvee, cls, year)
        for _ in range(t.triplets):
            cls = classes[0]
            producer = producer_name(rng, t.country, t.region, t.colour, taken)
            cuvee = rng.choice(cuvee_pool)
            vint = cls[3].get("vint", t.vint)
            years = list(range(vint[0], vint[1] + 1))
            if len(years) < 3:
                years = list(range(vint[1] - 2, vint[1] + 1))
            years = sorted(rng.sample(years, 3))
            offsets = rng.sample([-0.3, -0.15, 0.0, 0.15, 0.3], 3)
            u = rng.random()
            first = None
            for year, off in zip(years, offsets):
                make_one(t, producer, cuvee, cls, year, rating_offset=off, price_factor=1 + 1.1 * off, u=u,
                         same_as=first)
                first = first or wines[-1]
            trio = wines[-3:]
            # ratings and prices must all differ, otherwise the test would be meaningless
            for field, step in (("community_avg_rating", 0.1), ("price_cents", 100)):
                for _ in range(20):
                    values = [w[field] for w in trio]
                    if len(set(values)) == 3:
                        break
                    seen = set()
                    for w in trio:
                        while w[field] in seen:
                            w[field] = round(w[field] + step, 1) if field.startswith("comm") else w[field] + step
                        seen.add(w[field])
    return wines


C0 = (None, 1.0, 1.0, {})


def noted_tags(text, tags):
    """Aroma words the note really contains (longest tag first, whole words, faults ignored)."""
    work = " " + text.lower() + " "
    found = set()
    for tag in sorted(tags, key=len, reverse=True):
        pattern = re.compile(r"(?<![^\W\d_])" + re.escape(tag) + r"(?![^\W\d_])")
        if pattern.search(work):
            work = pattern.sub(" ", work)
            if tags[tag]["family"] != "Faults":
                found.add(tag)
    return found


def finish(wines, vocab):
    rng = random.Random(SEED + 1)
    wines.sort(key=lambda w: (fold(w["name"]), w["vintage"] or 0))
    for i, w in enumerate(wines, 1):
        w["wine_id"] = f"W-{i:03d}"
    # tasting notes ------------------------------------------------------------------------
    notes_path = ROOT / "data" / "tasting_notes.json"
    chosen = sorted(random.Random(SEED + 2).sample([w["wine_id"] for w in wines], N_NOTES))
    notes = json.loads(notes_path.read_text(encoding="utf-8")) if notes_path.exists() else {}
    by_id = {w["wine_id"]: w for w in wines}
    if notes:
        assert set(notes) == set(chosen), f"notes keys differ from selection: {sorted(set(notes) ^ set(chosen))}"
        tags = {e["tag"]: e for e in vocab}
        for wid, n in notes.items():
            assert by_id[wid]["name"] == n["name"] and by_id[wid]["vintage"] == n.get("vintage"), \
                f"note {wid} was written for another wine: {n['name']}"
            assert 1.0 <= n["rating"] <= 5.0 and (n["rating"] * 2) % 1 == 0, wid
            assert 2 <= len(n["aromas"]) <= 5, wid
            for tag in n["aromas"]:
                assert tag in tags and tags[tag]["family"] != "Faults", f"{wid}: bad tag {tag}"
            found = noted_tags(n["note"], tags)
            assert found == set(n["aromas"]), f"{wid}: note mentions {sorted(found)} but aromas are {sorted(n['aromas'])}"
    for w in wines:
        n = notes.get(w["wine_id"])
        w["user_review"] = n["note"] if n else None
        w["user_rating"] = n["rating"] if n else None
        stated = sorted(set(n["aromas"])) if n else []
        guesses = [g for g in w.pop("guesses") if g not in stated]
        w["flavours"] = ([{"tag": t, "provenance": "stated"} for t in stated]
                         + [{"tag": t, "provenance": "guess"} for t in guesses])
        w["inventory_synthetic"] = 1
        w["profile_source"] = "demo profile: typical for grape and style, not measured"
        w["search_text"] = fold(" ".join([w["name"], w["winery"], w["appellation"], w["region"], w["country"],
                                          " ".join(w["grapes"]), w["classification"] or ""]))
        w["attributes"] = {"brand": w["winery"], "type": w["wine_type"], "country": w["country"],
                           "region": w["region"], "appellation": w["appellation"],
                           "source": "fictional cave. demo catalogue (make_hec_catalog.py)",
                           "flavours_stated": stated, "flavours_inferred": guesses}
        w.pop("_tier", None)
        w.pop("_triplet", None)
    return chosen, by_id


def main():
    selection_only = "--selection" in sys.argv
    old = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
    vocab = old["flavour_vocabulary"]
    wines = build()
    triplet_ids = None
    chosen, by_id = finish(wines, vocab)
    if selection_only:
        for wid in chosen:
            w = by_id[wid]
            print(json.dumps({"id": wid, "name": w["name"], "vintage": w["vintage"], "type": w["wine_type"],
                              "app": w["appellation"], "cls": w["classification"], "grapes": w["grapes"],
                              "price": w["price_cents"] / 100, "sw": w["sweetness"], "bo": w["body"],
                              "ac": w["acidity"], "ta": w["tannin"], "fr": w["fruitiness"],
                              "food": w["pairings"], "guess": [f["tag"] for f in w["flavours"]]}, ensure_ascii=False))
        return
    snapshot = {
        "source_url": "fictional demo catalogue generated by make_hec_catalog.py",
        "source_commit": "hec-cave-demo-v1",
        "inventory_note": "All wines, producers, vintages, prices, stock and ratings are invented for the demo.",
        "ratings_note": "Taster and community ratings are invented. Regions, appellations and grapes are real.",
        "wines": wines,
        "flavour_vocabulary": vocab,
        "food_vocabulary": [{"food": f, "group": g} for f, g in FOODS],
    }
    out = ROOT / "data" / "catalog.json"
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with open(ROOT / "data" / "catalog_overview.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["wine_id", "name", "vintage", "type", "country", "region", "appellation", "classification",
                     "grapes", "price_eur", "stock", "community", "taster", "sweet", "body", "acid", "tannin", "fruit",
                     "pairings"])
        for w in wines:
            wr.writerow([w["wine_id"], w["name"], w["vintage"], w["wine_type"], w["country"], w["region"],
                         w["appellation"], w["classification"], " + ".join(w["grapes"]), w["price_cents"] / 100,
                         w["stock"], w["community_avg_rating"], w["user_rating"], w["sweetness"], w["body"],
                         w["acidity"], w["tannin"], w["fruitiness"], ", ".join(w["pairings"])])
    print(f"{len(wines)} wines written to {out}")


if __name__ == "__main__":
    main()
