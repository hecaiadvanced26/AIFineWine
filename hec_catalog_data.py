"""Reference tables for the fictional cave. catalogue (used by make_hec_catalog.py).

What is real and what is invented
- Real: country / region / appellation / grape pairings (taken from the Patroon wine list and the
  GuildSomm grape profiles supplied with the course, plus general wine knowledge where noted).
- Estimated by us, NOT from a source: the 1-5 structure ranges of grapes that are not among the 12
  GuildSomm profiles, and every food pairing.
- Invented: producers, cuvee names, vintages per bottle, prices, stock, ratings, tasting notes.

Scales (1-5): sweetness 1 bone dry ... 5 very sweet; body 1 light ... 5 full; acidity 1 soft ... 5 racy;
tannin 1 silky ... 5 grippy; fruitiness 1 subtle ... 5 very fruit-forward.
"""

# --- food vocabulary (tag, group) ---------------------------------------------------------------
FOODS = [
    ("aperitif", "occasion"), ("celebration", "occasion"),
    ("oysters", "seafood"), ("shellfish", "seafood"), ("white fish", "seafood"),
    ("grilled fish", "seafood"), ("salmon", "seafood"), ("sushi", "seafood"),
    ("salad", "vegetarian"), ("vegetables", "vegetarian"), ("mushrooms", "vegetarian"),
    ("goat cheese", "cheese"), ("soft cheese", "cheese"), ("hard cheese", "cheese"), ("blue cheese", "cheese"),
    ("charcuterie", "meat"), ("roast chicken", "meat"), ("pork", "meat"), ("duck", "meat"),
    ("lamb", "meat"), ("steak", "meat"), ("roast beef", "meat"), ("game meat", "meat"),
    ("barbecue", "meat"), ("foie gras", "meat"),
    ("risotto", "italian"), ("tomato pasta", "italian"), ("cream pasta", "italian"), ("pizza", "italian"),
    ("spicy asian", "spicy"), ("curry", "spicy"), ("tapas", "spanish"),
    ("fruit dessert", "dessert"), ("chocolate", "dessert"), ("pastry", "dessert"),
]

# --- grapes -----------------------------------------------------------------------------------
# name: (body, acidity, tannin or None, fruitiness, typical aroma tags, typical food tags)
# Ranges are (low, high) on the 1-5 scale. Marked [GS] = read off the GuildSomm chart, else our estimate.
G = {}


def grape(name, body, acid, tannin, fruit, aromas, foods):
    G[name] = dict(body=body, acid=acid, tannin=tannin, fruit=fruit, aromas=aromas, foods=foods)


# whites
grape("Chardonnay", (2, 5), (3, 5), None, (2, 4),   # [GS]
      ["apple", "pear", "lemon", "butter", "toast", "vanilla", "peach"],
      ["white fish", "shellfish", "roast chicken", "cream pasta", "soft cheese", "risotto", "salmon"])
grape("Sauvignon Blanc", (1, 3), (3, 5), None, (3, 5),   # [GS]
      ["grapefruit", "gooseberry", "cut grass", "passion fruit", "lime", "flint"],
      ["goat cheese", "salad", "white fish", "shellfish", "vegetables", "sushi"])
grape("Riesling", (1, 3), (4, 5), None, (3, 5),   # [GS]
      ["lime", "green apple", "peach", "flint", "lemon"],
      ["spicy asian", "sushi", "pork", "white fish", "curry", "aperitif"])
grape("Chenin Blanc", (2, 4), (3, 5), None, (3, 4),   # [GS]
      ["apple", "pear", "honeysuckle", "lemon", "almond"],
      ["pork", "roast chicken", "goat cheese", "white fish", "spicy asian", "fruit dessert"])
grape("Pinot Gris", (2, 4), (2, 3), None, (3, 4),
      ["pear", "apple", "peach", "almond"],
      ["risotto", "white fish", "cream pasta", "roast chicken", "aperitif", "salad"])
grape("Pinot Blanc", (2, 3), (3, 4), None, (2, 4),
      ["apple", "pear", "almond", "lemon"],
      ["white fish", "salad", "aperitif", "cream pasta", "risotto"])
grape("Gewurztraminer", (3, 5), (1, 3), None, (4, 5),
      ["lychee", "rose", "orange peel", "honeysuckle", "peach"],
      ["spicy asian", "curry", "soft cheese", "pork", "foie gras"])
grape("Viognier", (3, 5), (1, 3), None, (4, 5),
      ["peach", "dried apricot", "honeysuckle", "orange blossom"],
      ["spicy asian", "curry", "roast chicken", "shellfish", "pork"])
grape("Marsanne", (3, 5), (2, 3), None, (2, 4),
      ["pear", "almond", "honeysuckle", "hazelnut"],
      ["roast chicken", "cream pasta", "white fish", "soft cheese"])
grape("Roussanne", (3, 5), (2, 4), None, (2, 4),
      ["pear", "hazelnut", "honeysuckle", "orange blossom"],
      ["roast chicken", "shellfish", "soft cheese", "mushrooms"])
grape("Grenache Blanc", (3, 4), (2, 3), None, (2, 4),
      ["pear", "fennel", "lemon", "almond"],
      ["grilled fish", "tapas", "salad", "shellfish"])
grape("Clairette", (2, 3), (2, 3), None, (2, 3),
      ["lemon", "fennel", "pear"],
      ["grilled fish", "tapas", "salad", "shellfish"])
grape("Semillon", (3, 5), (2, 4), None, (3, 4),
      ["lemon", "honeysuckle", "dried apricot", "orange peel"],
      ["shellfish", "white fish", "roast chicken", "soft cheese"])
grape("Melon de Bourgogne", (1, 2), (4, 5), None, (2, 3),
      ["lemon", "green apple", "iodine", "flint"],
      ["oysters", "shellfish", "white fish", "salad", "aperitif"])
grape("Jacquere", (1, 2), (3, 5), None, (2, 3),
      ["lemon", "green apple", "flint", "hawthorn"],
      ["hard cheese", "salad", "white fish", "aperitif"])
grape("Savagnin", (3, 4), (4, 5), None, (2, 3),
      ["almond", "hazelnut", "apple", "lemon"],
      ["hard cheese", "roast chicken", "cream pasta", "mushrooms"])
grape("Albarino", (2, 3), (4, 5), None, (3, 4),
      ["peach", "lemon", "grapefruit", "jasmine"],
      ["shellfish", "oysters", "grilled fish", "sushi", "tapas"])
grape("Verdejo", (2, 3), (3, 4), None, (3, 4),
      ["grapefruit", "fennel", "lime", "melon"],
      ["salad", "grilled fish", "tapas", "vegetables", "goat cheese"])
grape("Viura", (2, 3), (3, 4), None, (2, 3),
      ["apple", "lemon", "hay"],
      ["tapas", "grilled fish", "roast chicken", "vegetables"])
grape("Loureiro", (1, 2), (4, 5), None, (3, 4),
      ["lemon", "lime", "orange blossom", "peach"],
      ["shellfish", "salad", "grilled fish", "sushi", "aperitif"])
grape("Arinto", (1, 3), (4, 5), None, (2, 3),
      ["lemon", "lime", "green apple", "flint"],
      ["shellfish", "grilled fish", "salad", "oysters"])
grape("Encruzado", (3, 4), (3, 4), None, (2, 3),
      ["pear", "lemon", "hazelnut"],
      ["roast chicken", "grilled fish", "soft cheese", "cream pasta"])
grape("Gruner Veltliner", (2, 4), (3, 5), None, (2, 4),
      ["green apple", "lime", "pepper", "grapefruit"],
      ["pork", "vegetables", "salad", "white fish", "roast chicken"])
grape("Cortese", (1, 3), (3, 5), None, (2, 3),
      ["lemon", "green apple", "flint", "almond"],
      ["white fish", "shellfish", "risotto", "salad", "aperitif"])
grape("Arneis", (2, 3), (2, 4), None, (2, 4),
      ["pear", "almond", "peach", "orange blossom"],
      ["risotto", "cream pasta", "white fish", "vegetables", "soft cheese"])
grape("Garganega", (2, 3), (3, 4), None, (2, 3),
      ["almond", "pear", "lemon", "melon"],
      ["risotto", "white fish", "cream pasta", "salad"])
grape("Verdicchio", (2, 3), (4, 5), None, (2, 3),
      ["lemon", "almond", "green apple", "fennel"],
      ["risotto", "white fish", "grilled fish", "shellfish"])
grape("Fiano", (3, 4), (3, 4), None, (2, 4),
      ["pear", "hazelnut", "honeysuckle", "orange peel"],
      ["risotto", "white fish", "roast chicken", "soft cheese"])
grape("Greco", (3, 4), (3, 5), None, (2, 4),
      ["peach", "lemon", "almond", "flint"],
      ["shellfish", "white fish", "pizza", "vegetables"])
grape("Vermentino", (2, 3), (3, 4), None, (2, 4),
      ["lemon", "grapefruit", "fennel", "almond"],
      ["grilled fish", "shellfish", "salad", "tapas", "pizza"])
grape("Carricante", (2, 3), (4, 5), None, (2, 3),
      ["lemon", "flint", "green apple", "iodine"],
      ["shellfish", "grilled fish", "vegetables"])
grape("Friulano", (3, 4), (2, 3), None, (2, 3),
      ["almond", "pear", "fennel", "apple"],
      ["risotto", "charcuterie", "white fish", "vegetables"])
grape("Torrontes", (2, 3), (2, 3), None, (4, 5),
      ["rose", "peach", "jasmine", "orange blossom"],
      ["spicy asian", "curry", "salad", "aperitif"])
grape("Assyrtiko", (3, 4), (4, 5), None, (2, 3),
      ["lemon", "flint", "iodine", "grapefruit"],
      ["grilled fish", "shellfish", "salad", "vegetables", "tapas"])
grape("Glera", (1, 2), (3, 4), None, (3, 4),
      ["green apple", "pear", "peach", "orange blossom"],
      ["aperitif", "celebration", "tapas", "pizza", "fruit dessert"])
grape("Xarel-lo", (2, 3), (3, 4), None, (2, 3),
      ["apple", "lemon", "bread", "pear"],
      ["aperitif", "tapas", "shellfish", "celebration"])
grape("Macabeo", (2, 3), (3, 4), None, (2, 3),
      ["apple", "lemon", "bread", "pear"],
      ["aperitif", "tapas", "shellfish", "celebration"])
grape("Parellada", (1, 2), (3, 4), None, (2, 3),
      ["apple", "lemon", "bread", "pear"],
      ["aperitif", "tapas", "shellfish", "celebration"])
grape("Moscato", (1, 2), (2, 3), None, (4, 5),
      ["peach", "orange blossom", "lychee", "pear"],
      ["fruit dessert", "pastry", "aperitif", "celebration", "blue cheese"])
grape("Rolle", (2, 3), (3, 4), None, (2, 3),
      ["lemon", "grapefruit", "fennel"], ["grilled fish", "salad", "aperitif"])

# reds
grape("Pinot Noir", (2, 4), (4, 5), (2, 4), (3, 4),   # [GS]
      ["cherry", "raspberry", "strawberry", "clove", "violet"],
      ["duck", "mushrooms", "roast chicken", "salmon", "soft cheese", "risotto"])
grape("Pinot Meunier", (2, 3), (4, 5), (2, 3), (3, 4),
      ["apple", "strawberry", "bread", "pear"], ["aperitif", "celebration", "charcuterie"])
grape("Gamay", (1, 3), (3, 5), (1, 3), (4, 5),
      ["strawberry", "raspberry", "cherry", "banana", "violet"],
      ["charcuterie", "roast chicken", "pork", "soft cheese", "pizza", "tomato pasta"])
grape("Cabernet Sauvignon", (3, 5), (3, 4), (4, 5), (3, 4),   # [GS]
      ["blackcurrant", "cedar", "tobacco", "blackberry", "bell pepper", "vanilla"],
      ["steak", "lamb", "roast beef", "hard cheese", "game meat", "barbecue"])
grape("Merlot", (3, 5), (2, 4), (3, 4), (3, 5),   # [GS]
      ["plum", "blackberry", "chocolate", "cherry", "cedar"],
      ["roast beef", "pork", "duck", "mushrooms", "tomato pasta", "hard cheese"])
grape("Cabernet Franc", (2, 4), (3, 5), (3, 4), (3, 4),
      ["raspberry", "bell pepper", "violet", "blackcurrant", "pepper"],
      ["pork", "roast chicken", "duck", "charcuterie", "goat cheese", "lamb"])
grape("Syrah", (3, 5), (3, 4), (3, 5), (3, 4),   # [GS]
      ["blackberry", "pepper", "smoke", "violet", "liquorice", "plum"],
      ["barbecue", "lamb", "steak", "game meat", "charcuterie", "hard cheese"])
grape("Grenache", (4, 5), (2, 4), (2, 4), (3, 5),   # [GS]
      ["strawberry", "raspberry", "pepper", "liquorice", "plum", "thyme"],
      ["barbecue", "lamb", "tomato pasta", "pork", "tapas", "charcuterie"])
grape("Mourvedre", (4, 5), (3, 4), (4, 5), (2, 4),
      ["blackberry", "pepper", "liquorice", "thyme", "smoke", "plum"],
      ["lamb", "game meat", "barbecue", "hard cheese", "mushrooms"])
grape("Carignan", (3, 4), (3, 5), (3, 4), (3, 4),
      ["blackberry", "thyme", "plum", "pepper"],
      ["barbecue", "charcuterie", "lamb", "tomato pasta", "pizza"])
grape("Cinsault", (1, 3), (3, 4), (1, 2), (4, 5),
      ["strawberry", "raspberry", "cherry", "rose"], ["grilled fish", "salad", "tapas", "aperitif"])
grape("Nebbiolo", (3, 4), (4, 5), (5, 5), (2, 3),   # [GS]
      ["cherry", "rose", "tar", "liquorice", "violet"],
      ["risotto", "mushrooms", "roast beef", "game meat", "hard cheese", "steak"])
grape("Sangiovese", (3, 5), (4, 5), (4, 5), (3, 4),   # [GS]
      ["cherry", "plum", "tomato", "tobacco", "thyme"],
      ["tomato pasta", "pizza", "steak", "pork", "hard cheese", "charcuterie"])
grape("Tempranillo", (3, 5), (4, 5), (3, 4), (3, 4),   # [GS]
      ["cherry", "plum", "vanilla", "tobacco", "clove", "cedar"],
      ["lamb", "pork", "charcuterie", "tapas", "hard cheese", "steak"])
grape("Graciano", (3, 4), (4, 5), (3, 4), (3, 4),
      ["blackberry", "plum", "violet", "pepper"], ["lamb", "pork", "tapas", "hard cheese"])
grape("Mencia", (2, 3), (3, 5), (2, 3), (4, 5),
      ["raspberry", "blackberry", "violet", "pepper"],
      ["pork", "charcuterie", "roast chicken", "tapas", "duck"])
grape("Touriga Nacional", (4, 5), (3, 4), (4, 5), (3, 4),
      ["blackberry", "violet", "plum", "cedar"],
      ["steak", "lamb", "hard cheese", "barbecue", "game meat"])
grape("Touriga Franca", (3, 4), (3, 4), (3, 4), (3, 4),
      ["blackberry", "violet", "plum", "pepper"], ["steak", "lamb", "barbecue", "hard cheese"])
grape("Alicante Bouschet", (4, 5), (2, 3), (4, 5), (3, 4),
      ["blackberry", "plum", "prune", "chocolate"], ["steak", "barbecue", "lamb", "hard cheese"])
grape("Trincadeira", (3, 4), (3, 4), (3, 4), (3, 4),
      ["plum", "raspberry", "pepper", "thyme"], ["pork", "barbecue", "tapas", "charcuterie"])
grape("Malbec", (4, 5), (3, 4), (3, 5), (4, 5),
      ["plum", "blackberry", "violet", "chocolate", "smoke"],
      ["steak", "barbecue", "lamb", "roast beef", "hard cheese"])
grape("Tannat", (4, 5), (4, 5), (5, 5), (3, 4),
      ["blackberry", "plum", "smoke", "chocolate", "tar"],
      ["duck", "steak", "charcuterie", "barbecue", "hard cheese", "game meat"])
grape("Zinfandel", (4, 5), (3, 4), (3, 4), (4, 5),
      ["blackberry", "prune", "pepper", "raspberry", "liquorice", "clove"],
      ["barbecue", "pizza", "pork", "tomato pasta", "charcuterie", "steak"])
grape("Carmenere", (3, 5), (2, 3), (3, 4), (3, 4),
      ["bell pepper", "blackberry", "plum", "pepper", "chocolate"],
      ["lamb", "pork", "steak", "barbecue", "tapas"])
grape("Pinotage", (4, 5), (3, 4), (3, 5), (4, 5),
      ["plum", "blackberry", "smoke", "cherry"], ["barbecue", "pork", "lamb", "steak"])
grape("Blaufrankisch", (3, 4), (4, 5), (3, 4), (3, 4),
      ["blackberry", "cherry", "pepper", "violet"],
      ["pork", "duck", "roast chicken", "charcuterie", "hard cheese", "mushrooms"])
grape("Zweigelt", (2, 3), (3, 4), (2, 3), (4, 5),
      ["cherry", "raspberry", "pepper", "plum"],
      ["pork", "roast chicken", "charcuterie", "pizza", "tomato pasta"])
grape("Barbera", (3, 4), (4, 5), (1, 3), (4, 5),
      ["cherry", "plum", "blackberry", "liquorice"],
      ["pizza", "tomato pasta", "risotto", "charcuterie", "pork", "hard cheese"])
grape("Dolcetto", (2, 3), (2, 3), (3, 4), (3, 4),
      ["plum", "cherry", "almond", "liquorice"],
      ["pizza", "tomato pasta", "charcuterie", "pork", "risotto"])
grape("Corvina", (2, 3), (4, 5), (2, 3), (3, 4),
      ["cherry", "plum", "almond"], ["pizza", "tomato pasta", "risotto", "charcuterie"])
grape("Corvinone", (3, 4), (3, 4), (3, 4), (3, 4),
      ["cherry", "plum", "chocolate"], ["roast beef", "pork", "hard cheese"])
grape("Rondinella", (2, 3), (3, 4), (2, 3), (3, 4),
      ["cherry", "plum", "almond"], ["pizza", "tomato pasta", "charcuterie"])
grape("Montepulciano", (3, 4), (3, 4), (3, 4), (4, 5),
      ["plum", "cherry", "blackberry", "pepper"],
      ["pizza", "tomato pasta", "barbecue", "charcuterie", "lamb"])
grape("Primitivo", (4, 5), (2, 3), (3, 4), (4, 5),
      ["prune", "blackberry", "plum", "liquorice", "pepper"],
      ["barbecue", "pizza", "pork", "tomato pasta", "hard cheese"])
grape("Nerello Mascalese", (2, 3), (4, 5), (3, 4), (3, 4),
      ["cherry", "raspberry", "smoke", "thyme"],
      ["pork", "roast chicken", "mushrooms", "tomato pasta", "charcuterie"])
grape("Nero d'Avola", (3, 5), (3, 4), (3, 4), (4, 5),
      ["plum", "cherry", "pepper", "liquorice", "blackberry"],
      ["barbecue", "tomato pasta", "pizza", "lamb", "pork"])
grape("Aglianico", (4, 5), (4, 5), (4, 5), (3, 4),
      ["blackberry", "plum", "tar", "liquorice", "tobacco"],
      ["lamb", "game meat", "steak", "hard cheese", "barbecue"])
grape("Xinomavro", (3, 4), (4, 5), (4, 5), (3, 4),
      ["cherry", "tomato", "tobacco", "plum", "thyme"],
      ["lamb", "tomato pasta", "pork", "hard cheese", "mushrooms"])

# --- reference lists used by the generator ---------------------------------------------------
TIER_PRICE_EUR = {1: (6, 14), 2: (12, 26), 3: (22, 55), 4: (40, 110), 5: (100, 300)}


class T:
    """One appellation template. Fields follow make_hec_catalog.py."""

    def __init__(self, country, region, appellation, colour, grapes, tier, n, vint=(2020, 2022), triplets=0,
                 classes=None, shift=0, sweet=(1, 1), body=None, acid=None, tannin=None, fruit=None,
                 foods=None, nv=False, style=None, ml=750):
        self.__dict__.update(locals())
        del self.__dict__["self"]


def C(label, mult=1.0, weight=1.0, **mods):
    """A classification / bottling level. mods: sweet=(lo,hi) body_add acid_add tannin_add vint=(lo,hi) nv ml foods"""
    return (label, mult, weight, mods)


TEMPLATES = [
    # ---------------------------------------------------------------- FRANCE - Burgundy reds
    T("France", "Burgundy", "Gevrey-Chambertin", "red", ["Pinot Noir"], 4, 4, (2019, 2022), shift=0,
      classes=[C(None, 1.0, 2), C("1er Cru", 1.9, 1.5, body_add=1, tannin_add=1)]),
    T("France", "Burgundy", "Chambolle-Musigny", "red", ["Pinot Noir"], 4, 2, (2019, 2022),
      classes=[C(None, 1.0, 2), C("1er Cru", 1.9, 1)]),
    T("France", "Burgundy", "Nuits-Saint-Georges", "red", ["Pinot Noir"], 4, 2, (2019, 2022),
      classes=[C(None, 1.0, 2), C("1er Cru", 1.8, 1, tannin_add=1)]),
    T("France", "Burgundy", "Pommard", "red", ["Pinot Noir"], 4, 2, (2019, 2022), classes=[C(None, 1.0, 1)]),
    T("France", "Burgundy", "Volnay", "red", ["Pinot Noir"], 4, 1, (2019, 2022), classes=[C("1er Cru", 1.8, 1)]),
    T("France", "Burgundy", "Bourgogne Rouge", "red", ["Pinot Noir"], 2, 2, (2020, 2023)),
    # Beaujolais
    T("France", "Beaujolais", "Morgon", "red", ["Gamay"], 2, 2, (2021, 2023)),
    T("France", "Rhone Valley", "Chateauneuf-du-Pape", "red", ["Grenache", "Syrah", "Mourvedre"], 4, 4, (2019, 2022),
      triplets=1),
    T("France", "Rhone Valley", "Gigondas", "red", ["Grenache", "Syrah", "Mourvedre"], 3, 2, (2019, 2022)),
    T("France", "Rhone Valley", "Cote-Rotie", "red", ["Syrah"], 5, 1, (2018, 2021)),
    T("France", "Rhone Valley", "Hermitage", "red", ["Syrah"], 5, 1, (2017, 2021)),
    T("France", "Rhone Valley", "Crozes-Hermitage", "red", ["Syrah"], 3, 2, (2020, 2022)),
    T("France", "Rhone Valley", "Cotes du Rhone", "red", ["Grenache", "Syrah", "Mourvedre"], 1, 3, (2021, 2023)),
    # Bordeaux
    T("France", "Bordeaux", "Pauillac", "red", ["Cabernet Sauvignon", "Merlot", "Cabernet Franc"], 5, 2, (2016, 2020)),
    T("France", "Bordeaux", "Saint-Estephe", "red", ["Cabernet Sauvignon", "Merlot"], 4, 2, (2016, 2020)),
    T("France", "Bordeaux", "Saint-Julien", "red", ["Cabernet Sauvignon", "Merlot"], 4, 1, (2016, 2020)),
    T("France", "Bordeaux", "Margaux", "red", ["Cabernet Sauvignon", "Merlot"], 4, 2, (2016, 2020)),
    T("France", "Bordeaux", "Haut-Medoc", "red", ["Cabernet Sauvignon", "Merlot"], 2, 4, (2017, 2021), triplets=1),
    T("France", "Bordeaux", "Pessac-Leognan", "red", ["Cabernet Sauvignon", "Merlot"], 4, 1, (2016, 2020)),
    T("France", "Bordeaux", "Saint-Emilion Grand Cru", "red", ["Merlot", "Cabernet Franc"], 4, 2, (2016, 2020)),
    T("France", "Bordeaux", "Pomerol", "red", ["Merlot", "Cabernet Franc"], 5, 2, (2016, 2020)),
    T("France", "Bordeaux", "Bordeaux Superieur", "red", ["Merlot", "Cabernet Sauvignon"], 1, 2, (2019, 2022)),
    # Loire / South-West / South
    T("France", "Loire Valley", "Chinon", "red", ["Cabernet Franc"], 2, 2, (2020, 2022)),
    T("France", "South-West France", "Cahors", "red", ["Malbec", "Merlot"], 2, 2, (2018, 2021)),
    T("France", "Languedoc-Roussillon", "Minervois", "red", ["Syrah", "Grenache", "Carignan"], 1, 2, (2020, 2022)),
    T("France", "Provence", "Bandol", "red", ["Mourvedre", "Grenache"], 4, 1, (2018, 2020)),
    # ---------------------------------------------------------------- ITALY reds
    T("Italy", "Piedmont", "Barolo", "red", ["Nebbiolo"], 4, 4, (2016, 2020), triplets=1,
      classes=[C(None, 1.0, 3), C("Riserva", 1.7, 1, vint=(2013, 2016), body_add=1)]),
    T("Italy", "Piedmont", "Barbaresco", "red", ["Nebbiolo"], 4, 2, (2018, 2020)),
    T("Italy", "Piedmont", "Langhe Nebbiolo", "red", ["Nebbiolo"], 2, 1, (2020, 2022)),
    T("Italy", "Piedmont", "Barbera d'Asti", "red", ["Barbera"], 2, 2, (2020, 2022)),
    T("Italy", "Piedmont", "Dolcetto d'Alba", "red", ["Dolcetto"], 1, 1, (2021, 2023)),
    T("Italy", "Tuscany", "Chianti Classico", "red", ["Sangiovese"], 2, 4, (2019, 2022), triplets=1,
      classes=[C(None, 1.0, 3), C("Riserva", 1.6, 1, vint=(2018, 2020), body_add=1), C("Gran Selezione", 2.4, 0.6, vint=(2017, 2019), body_add=1)]),
    T("Italy", "Tuscany", "Brunello di Montalcino", "red", ["Sangiovese"], 4, 2, (2015, 2019)),
    T("Italy", "Tuscany", "Bolgheri Superiore", "red", ["Cabernet Sauvignon", "Merlot", "Cabernet Franc"], 5, 1, (2017, 2020)),
    T("Italy", "Veneto", "Amarone della Valpolicella", "red", ["Corvina", "Corvinone", "Rondinella"], 4, 2, (2015, 2018),
      body=(5, 5), tannin=(4, 5), acid=(3, 4), sweet=(2, 2), fruit=(4, 5),
      foods=["roast beef", "game meat", "hard cheese", "steak", "mushrooms"]),
    T("Italy", "Veneto", "Valpolicella Ripasso", "red", ["Corvina", "Rondinella"], 2, 2, (2019, 2021),
      body=(3, 4), sweet=(1, 2)),
    T("Italy", "Abruzzo", "Montepulciano d'Abruzzo", "red", ["Montepulciano"], 1, 2, (2020, 2022)),
    T("Italy", "Puglia", "Primitivo di Manduria", "red", ["Primitivo"], 2, 1, (2020, 2022), shift=1),
    T("Italy", "Sicily", "Etna Rosso", "red", ["Nerello Mascalese"], 3, 1, (2019, 2021)),
    T("Italy", "Campania", "Taurasi", "red", ["Aglianico"], 3, 1, (2016, 2018)),
    T("Spain", "Rioja", "Rioja", "red", ["Tempranillo", "Grenache", "Graciano"], 2, 5, (2019, 2022), triplets=1,
      classes=[C("Crianza", 1.0, 3, vint=(2020, 2022)), C("Reserva", 1.5, 2, vint=(2017, 2020), body_add=1),
               C("Gran Reserva", 2.4, 1, vint=(2012, 2016), body_add=1, acid_add=-1)]),
    T("Spain", "Ribera del Duero", "Ribera del Duero", "red", ["Tempranillo"], 3, 3, (2018, 2021), shift=1),
    T("Spain", "Catalonia", "Priorat", "red", ["Grenache", "Carignan"], 4, 1, (2018, 2020), shift=1),
    T("Spain", "Castilla y Leon", "Bierzo", "red", ["Mencia"], 2, 1, (2020, 2022)),
    T("Portugal", "Douro", "Douro", "red", ["Touriga Nacional", "Touriga Franca", "Tempranillo"], 2, 3, (2018, 2021), shift=1),
    T("Austria", "Burgenland", "Burgenland", "red", ["Blaufrankisch"], 2, 1, (2019, 2021)),
    T("United States", "California", "Napa Valley", "red", ["Cabernet Sauvignon"], 5, 4, (2018, 2021), triplets=1, shift=1),
    T("United States", "California", "Sonoma Coast", "red", ["Pinot Noir"], 4, 1, (2020, 2022)),
    T("United States", "California", "Russian River Valley", "red", ["Pinot Noir"], 4, 1, (2020, 2022), shift=1),
    T("United States", "Oregon", "Willamette Valley", "red", ["Pinot Noir"], 3, 2, (2020, 2022)),
    T("United States", "California", "Paso Robles", "red", ["Zinfandel"], 2, 1, (2020, 2022), shift=1),
    T("United States", "Washington", "Columbia Valley", "red", ["Cabernet Sauvignon", "Merlot"], 3, 1, (2019, 2021)),
    T("Australia", "South Australia", "Barossa Valley", "red", ["Syrah"], 3, 2, (2018, 2021), shift=1),
    T("Australia", "South Australia", "McLaren Vale", "red", ["Grenache", "Syrah", "Mourvedre"], 3, 1, (2019, 2021), shift=1),
    T("Australia", "Victoria", "Yarra Valley", "red", ["Pinot Noir"], 3, 1, (2020, 2022)),
    T("New Zealand", "Central Otago", "Central Otago", "red", ["Pinot Noir"], 3, 2, (2020, 2022)),
    T("Chile", "Colchagua Valley", "Colchagua Valley", "red", ["Carmenere"], 2, 2, (2019, 2021), shift=1),
    T("Argentina", "Mendoza", "Mendoza", "red", ["Malbec"], 1, 3, (2020, 2022), shift=1),
    T("Argentina", "Mendoza", "Valle de Uco", "red", ["Malbec"], 3, 1, (2019, 2021)),
    T("South Africa", "Stellenbosch", "Stellenbosch", "red", ["Cabernet Sauvignon"], 3, 1, (2018, 2020)),
    T("South Africa", "Coastal Region", "Paarl", "red", ["Pinotage"], 2, 1, (2019, 2021), shift=1),
    T("South Africa", "Swartland", "Swartland", "red", ["Syrah"], 3, 1, (2019, 2021), shift=1),
    T("Uruguay", "Canelones", "Canelones", "red", ["Tannat"], 2, 1, (2018, 2021)),
    T("Greece", "Macedonia", "Naoussa", "red", ["Xinomavro"], 3, 1, (2018, 2020)),

    # ---------------------------------------------------------------- WHITES - France
    T("France", "Burgundy", "Chablis", "white", ["Chardonnay"], 3, 5, (2021, 2023), triplets=1, shift=-1,
      classes=[C(None, 1.0, 3, body_add=-1), C("1er Cru", 1.9, 1.5), C("Grand Cru", 4.5, 0.2, vint=(2019, 2021), body_add=1)]),
    T("France", "Burgundy", "Meursault", "white", ["Chardonnay"], 4, 2, (2020, 2022), body=(4, 5), acid=(3, 4),
      classes=[C(None, 1.0, 2), C("1er Cru", 1.8, 1)]),
    T("France", "Burgundy", "Puligny-Montrachet", "white", ["Chardonnay"], 5, 2, (2020, 2022),
      classes=[C(None, 1.0, 2), C("1er Cru", 1.7, 1)]),
    T("France", "Burgundy", "Chassagne-Montrachet", "white", ["Chardonnay"], 4, 1, (2020, 2022)),
    T("France", "Burgundy", "Saint-Aubin", "white", ["Chardonnay"], 3, 1, (2021, 2022)),
    T("France", "Burgundy", "Pouilly-Fuisse", "white", ["Chardonnay"], 3, 2, (2021, 2023)),
    T("France", "Burgundy", "Macon-Villages", "white", ["Chardonnay"], 1, 2, (2022, 2024)),
    T("France", "Burgundy", "Bourgogne Blanc", "white", ["Chardonnay"], 2, 2, (2021, 2023)),
    T("France", "Loire Valley", "Sancerre", "white", ["Sauvignon Blanc"], 3, 4, (2022, 2024), triplets=1, shift=-1),
    T("France", "Loire Valley", "Pouilly-Fume", "white", ["Sauvignon Blanc"], 3, 2, (2022, 2024)),
    T("France", "Loire Valley", "Vouvray", "white", ["Chenin Blanc"], 2, 3, (2019, 2023), shift=0,
      classes=[C("Sec", 1.0, 1.5, sweet=(1, 1)), C("Demi-Sec", 1.1, 1.5, sweet=(3, 3)), C("Moelleux", 1.5, 1, sweet=(4, 4), vint=(2018, 2020))]),
    T("France", "Loire Valley", "Savennieres", "white", ["Chenin Blanc"], 3, 1, (2020, 2022), body=(3, 4)),
    T("France", "Loire Valley", "Muscadet Sevre-et-Maine", "white", ["Melon de Bourgogne"], 1, 2, (2022, 2024)),
    T("France", "Alsace", "Alsace Riesling", "white", ["Riesling"], 3, 3, (2020, 2023), body=(2, 3)),
    T("France", "Alsace", "Alsace Gewurztraminer", "white", ["Gewurztraminer"], 3, 2, (2020, 2023), sweet=(2, 3)),
    T("France", "Alsace", "Alsace Pinot Gris", "white", ["Pinot Gris"], 3, 1, (2020, 2023), sweet=(2, 3)),
    T("France", "Rhone Valley", "Condrieu", "white", ["Viognier"], 5, 1, (2021, 2023)),
    T("France", "Rhone Valley", "Chateauneuf-du-Pape", "white", ["Grenache Blanc", "Roussanne", "Clairette"], 4, 1, (2020, 2022)),
    T("France", "Bordeaux", "Pessac-Leognan", "white", ["Sauvignon Blanc", "Semillon"], 4, 1, (2020, 2022), body=(3, 4)),
    T("France", "Bordeaux", "Sauternes", "white", ["Semillon", "Sauvignon Blanc"], 4, 2, (2015, 2019), sweet=(5, 5),
      body=(4, 5), acid=(3, 4), fruit=(4, 5), ml=375,
      foods=["foie gras", "blue cheese", "fruit dessert", "pastry"]),
    T("France", "Jura", "Arbois", "white", ["Chardonnay", "Savagnin"], 3, 1, (2019, 2021)),
    T("Italy", "Piedmont", "Gavi", "white", ["Cortese"], 2, 2, (2022, 2024)),
    T("Italy", "Piedmont", "Roero Arneis", "white", ["Arneis"], 2, 1, (2022, 2024)),
    T("Italy", "Veneto", "Soave Classico", "white", ["Garganega"], 1, 2, (2022, 2024)),
    T("Italy", "Alto Adige", "Alto Adige Pinot Grigio", "white", ["Pinot Gris"], 2, 2, (2022, 2024)),
    T("Italy", "Alto Adige", "Alto Adige Gewurztraminer", "white", ["Gewurztraminer"], 3, 1, (2021, 2023), sweet=(2, 3)),
    T("Italy", "Marche", "Verdicchio dei Castelli di Jesi", "white", ["Verdicchio"], 1, 1, (2022, 2024)),
    T("Italy", "Campania", "Fiano di Avellino", "white", ["Fiano"], 2, 1, (2021, 2023)),
    T("Italy", "Sardinia", "Vermentino di Gallura", "white", ["Vermentino"], 2, 1, (2022, 2024)),
    T("Italy", "Sicily", "Etna Bianco", "white", ["Carricante"], 3, 1, (2021, 2023)),
    T("Spain", "Galicia", "Rias Baixas", "white", ["Albarino"], 2, 3, (2022, 2024)),
    T("Spain", "Castilla y Leon", "Rueda", "white", ["Verdejo"], 1, 2, (2022, 2024)),
    T("Portugal", "Minho", "Vinho Verde", "white", ["Loureiro", "Arinto"], 1, 2, (2023, 2024), fruit=(3, 4)),
    T("Germany", "Mosel", "Mosel Riesling", "white", ["Riesling"], 2, 5, (2020, 2023), triplets=1, shift=-1,
      classes=[C("Kabinett", 1.0, 2, sweet=(2, 3), body_add=-1), C("Spatlese", 1.4, 2, sweet=(3, 4)), C("Trocken", 1.0, 1.5, sweet=(1, 1))]),
    T("Germany", "Rheingau", "Rheingau Riesling", "white", ["Riesling"], 3, 1, (2020, 2022), sweet=(1, 2)),
    T("Germany", "Pfalz", "Pfalz Riesling", "white", ["Riesling"], 2, 1, (2021, 2023), sweet=(1, 2)),
    T("Austria", "Kamptal", "Kamptal", "white", ["Gruner Veltliner"], 2, 2, (2021, 2023)),
    T("United States", "California", "Sonoma Coast", "white", ["Chardonnay"], 4, 1, (2020, 2022)),
    T("United States", "California", "Russian River Valley", "white", ["Chardonnay"], 4, 1, (2020, 2022), shift=1),
    T("United States", "California", "Napa Valley", "white", ["Chardonnay"], 4, 1, (2020, 2022), shift=1),
    T("United States", "California", "Santa Barbara County", "white", ["Chardonnay"], 3, 1, (2021, 2023)),
    T("United States", "California", "Napa Valley", "white", ["Sauvignon Blanc"], 3, 1, (2022, 2024)),
    T("New Zealand", "Marlborough", "Marlborough", "white", ["Sauvignon Blanc"], 2, 3, (2023, 2024), shift=0, fruit=(4, 5)),
    T("Australia", "South Australia", "Clare Valley", "white", ["Riesling"], 2, 1, (2021, 2023)),
    T("Australia", "South Australia", "Adelaide Hills", "white", ["Chardonnay"], 3, 1, (2021, 2023)),
    T("Australia", "Western Australia", "Margaret River", "white", ["Chardonnay"], 3, 1, (2021, 2023)),
    T("Chile", "Casablanca Valley", "Casablanca Valley", "white", ["Sauvignon Blanc"], 1, 1, (2023, 2024)),
    T("Argentina", "Salta", "Salta", "white", ["Torrontes"], 1, 1, (2023, 2024)),
    T("South Africa", "Swartland", "Swartland", "white", ["Chenin Blanc"], 2, 2, (2021, 2023), shift=1),
    T("Greece", "Cyclades", "Santorini", "white", ["Assyrtiko"], 3, 1, (2021, 2023)),

    # ---------------------------------------------------------------- ROSE
    T("France", "Provence", "Cotes de Provence", "rose", ["Grenache", "Cinsault", "Syrah", "Rolle"], 2, 4, (2024, 2025),
      body=(1, 3), acid=(3, 4), fruit=(3, 4), foods=["aperitif", "salad", "grilled fish", "tapas", "vegetables"]),
    T("France", "Provence", "Bandol", "rose", ["Mourvedre", "Grenache", "Cinsault"], 3, 1, (2023, 2025),
      body=(2, 3), acid=(3, 4), fruit=(3, 4), foods=["grilled fish", "tapas", "salad", "shellfish"]),
    T("France", "Rhone Valley", "Tavel", "rose", ["Grenache", "Cinsault"], 2, 1, (2023, 2025),
      body=(3, 4), acid=(3, 4), fruit=(3, 5), foods=["barbecue", "charcuterie", "tapas", "grilled fish"]),
    T("France", "Loire Valley", "Sancerre", "rose", ["Pinot Noir"], 3, 1, (2023, 2025),
      body=(1, 3), acid=(4, 5), fruit=(3, 4), foods=["salad", "goat cheese", "salmon", "aperitif"]),
    T("France", "Provence", "Coteaux d'Aix-en-Provence", "rose", ["Grenache", "Cinsault", "Syrah"], 1, 1, (2024, 2025),
      body=(1, 3), acid=(3, 4), fruit=(3, 4), foods=["aperitif", "salad", "grilled fish", "tapas"]),
    T("Spain", "Navarra", "Navarra", "rose", ["Grenache"], 1, 1, (2024, 2025),
      body=(2, 3), acid=(3, 4), fruit=(4, 5), foods=["tapas", "pizza", "charcuterie", "salad"]),
    T("Spain", "Rioja", "Rioja Rosado", "rose", ["Grenache", "Tempranillo"], 1, 1, (2023, 2025),
      body=(2, 3), acid=(3, 4), fruit=(3, 5), foods=["tapas", "charcuterie", "grilled fish", "salad"]),
    T("Italy", "Abruzzo", "Cerasuolo d'Abruzzo", "rose", ["Montepulciano"], 1, 1, (2023, 2025),
      body=(3, 4), acid=(3, 4), fruit=(4, 5), foods=["pizza", "tomato pasta", "charcuterie", "barbecue"]),
    T("Italy", "Veneto", "Bardolino Chiaretto", "rose", ["Corvina", "Rondinella"], 1, 1, (2024, 2025),
      body=(1, 2), acid=(3, 4), fruit=(3, 4), foods=["aperitif", "salad", "grilled fish", "risotto"]),
    T("Italy", "Tuscany", "Maremma Toscana", "rose", ["Sangiovese"], 2, 1, (2024, 2025),
      body=(2, 3), acid=(4, 5), fruit=(3, 4), foods=["salad", "grilled fish", "pizza", "tapas"]),
    T("United States", "Oregon", "Willamette Valley", "rose", ["Pinot Noir"], 3, 1, (2023, 2025),
      body=(2, 3), acid=(4, 5), fruit=(3, 4), foods=["salmon", "salad", "aperitif", "soft cheese"]),
    T("Germany", "Baden", "Baden", "rose", ["Pinot Noir"], 2, 1, (2023, 2025),
      body=(1, 3), acid=(4, 5), fruit=(3, 4), foods=["salad", "salmon", "aperitif", "pork"]),
    T("Austria", "Lower Austria", "Niederosterreich", "rose", ["Zweigelt"], 1, 1, (2024, 2025),
      body=(1, 3), acid=(3, 4), fruit=(4, 5), foods=["aperitif", "salad", "pork", "pizza"]),
    T("South Africa", "Swartland", "Swartland", "rose", ["Cinsault", "Syrah"], 2, 1, (2024, 2025),
      body=(2, 3), acid=(3, 4), fruit=(4, 5), foods=["salad", "grilled fish", "barbecue", "tapas"]),
    T("France", "Champagne", "Champagne", "sparkling", ["Chardonnay", "Pinot Noir", "Pinot Meunier"], 4, 6, (2012, 2016), nv=True,
      body=(2, 4), acid=(4, 5), fruit=(2, 3), sweet=(2, 2),
      foods=["celebration", "aperitif", "oysters", "shellfish", "soft cheese"],
      classes=[C("Brut", 1.0, 3, nv=True), C("Brut Nature", 1.1, 1, nv=True, sweet=(1, 1)),
               C("Extra Brut", 1.1, 1, nv=True, sweet=(1, 1)),
               C("Millesime", 1.8, 1.2, nv=False, body_add=1)]),
    T("France", "Champagne", "Champagne", "sparkling", ["Chardonnay"], 4, 2, (2013, 2016), nv=True, style="Blanc de Blancs",
      body=(2, 3), acid=(4, 5), fruit=(2, 3), sweet=(1, 2),
      foods=["oysters", "shellfish", "celebration", "aperitif", "white fish"]),
    T("France", "Champagne", "Champagne", "sparkling", ["Pinot Noir", "Pinot Meunier"], 4, 2, (2013, 2016), nv=True, style="Blanc de Noirs",
      body=(3, 4), acid=(4, 5), fruit=(3, 4), sweet=(2, 2),
      foods=["celebration", "salmon", "roast chicken", "charcuterie", "soft cheese"]),
    T("France", "Champagne", "Champagne", "sparkling", ["Pinot Noir", "Chardonnay", "Pinot Meunier"], 4, 2, (2013, 2016), nv=True, style="Rose",
      body=(3, 4), acid=(4, 5), fruit=(3, 5), sweet=(2, 2),
      foods=["celebration", "aperitif", "salmon", "sushi", "fruit dessert"]),
    T("France", "Alsace", "Cremant d'Alsace", "sparkling", ["Pinot Blanc", "Pinot Noir"], 2, 2, (2021, 2023), nv=True,
      body=(2, 3), acid=(3, 4), fruit=(3, 4), sweet=(2, 2), foods=["aperitif", "celebration", "salad", "white fish"]),
    T("France", "Alsace", "Cremant d'Alsace", "sparkling", ["Pinot Noir"], 2, 1, (2021, 2023), nv=True, style="Rose",
      body=(2, 3), acid=(3, 4), fruit=(4, 5), sweet=(2, 2), foods=["aperitif", "celebration", "salmon", "fruit dessert"]),
    T("France", "Loire Valley", "Cremant de Loire", "sparkling", ["Chenin Blanc", "Cabernet Franc", "Chardonnay"], 2, 1, (2021, 2023), nv=True,
      body=(2, 3), acid=(3, 5), fruit=(3, 4), sweet=(2, 2), foods=["aperitif", "celebration", "goat cheese", "white fish"]),
    T("France", "Burgundy", "Cremant de Bourgogne", "sparkling", ["Pinot Noir", "Chardonnay"], 2, 1, (2021, 2023), nv=True,
      body=(2, 3), acid=(3, 4), fruit=(3, 4), sweet=(2, 2), foods=["aperitif", "celebration", "soft cheese", "shellfish"]),
    T("Spain", "Catalonia", "Cava", "sparkling", ["Xarel-lo", "Macabeo", "Parellada"], 1, 3, (2021, 2023), nv=True,
      body=(2, 3), acid=(3, 4), fruit=(2, 3), sweet=(1, 2),
      classes=[C("Brut Nature Reserva", 1.3, 1, sweet=(1, 1)), C("Brut", 1.0, 2)]),
    T("Italy", "Veneto", "Prosecco", "sparkling", ["Glera"], 1, 2, (2023, 2024), nv=True,
      body=(1, 2), acid=(3, 4), fruit=(3, 4), sweet=(2, 3),
      classes=[C("Extra Dry", 1.0, 1.5, sweet=(3, 3)), C("Brut", 1.0, 2, sweet=(2, 2)), C("Superiore DOCG", 1.5, 1, sweet=(2, 3))]),
    T("Italy", "Lombardy", "Franciacorta", "sparkling", ["Chardonnay", "Pinot Noir"], 3, 2, (2018, 2020), nv=True,
      body=(2, 4), acid=(3, 4), fruit=(2, 3), sweet=(1, 2), foods=["celebration", "aperitif", "risotto", "shellfish", "white fish"]),
    T("Italy", "Piedmont", "Moscato d'Asti", "sparkling", ["Moscato"], 1, 1, (2024, 2025),
      body=(1, 1), acid=(2, 3), fruit=(5, 5), sweet=(4, 4), ml=750,
      foods=["fruit dessert", "pastry", "aperitif", "blue cheese"]),
    T("Germany", "Rheinhessen", "Sekt", "sparkling", ["Riesling"], 2, 1, (2020, 2022), nv=True,
      body=(1, 3), acid=(4, 5), fruit=(3, 4), sweet=(1, 2), foods=["aperitif", "celebration", "sushi", "white fish"]),
    T("England", "Sussex", "English Sparkling Wine", "sparkling", ["Chardonnay", "Pinot Noir", "Pinot Meunier"], 3, 2, (2017, 2019), nv=True,
      body=(2, 4), acid=(4, 5), fruit=(2, 3), sweet=(1, 2), foods=["celebration", "aperitif", "oysters", "salmon"]),
]
