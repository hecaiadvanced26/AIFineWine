# Demo prompts

Run `./start.sh` and open http://localhost:8000. The catalog is 200 real wines from the
taster's own Vivino tasting log. **Price, stock and bottle size are invented demo data.**
No real payment, email or shop delivery integration.

Expectations below were computed from a freshly seeded database (`data/demo_wines.json`),
not from a model run. They change if stock was already modified in your local `data/wines.db`.

## Main flow

1. “I'm looking for an Italian red wine with cherry aromas.”
   Expected (aroma written by the taster, in stock): W-149 Ponte Lungo Curioso Grand
   Edizione (€15.00), W-155 San Marzano Il Pumo Primitivo (€15.00), W-178 Hoffmann's
   Wein:Bar Montepulciano (€14.00), W-184 Tegut Bio Montepulciano Abruzzen Trocken (€12.00).
   Check that the answer says these aroma tags come from the taster's notes (the free-text reviews themselves are not in the catalog).
2. “Which is the cheapest one, and do you have five bottles?”
   Expected: W-184 (€12.00, 9 in stock).
3. “Prepare two bottles of W-001.”
   Expected: draft totaling €17.00 (2 × €8.50). No stock change until confirmation.
4. Click **Confirm order**.
   Expected: “Order confirmed” banner; local export only; W-001 stock goes 18 → 16.

Use **Cancel** for rehearsals without changing stock. Terminal equivalents:
`./start.sh --cli`, `/confirm`, `/cancel`.

## Other prompts

- “Best-rated white wines in stock.” — Top by taster_rating: W-152 Roche Mazet Cuvée
  Signature Chardonnay (4.8), then 4.7: W-048, W-125, W-143, W-145. It must say this is one
  person's rating.
- “How many Austrian wines are in stock?” — 9 (count query).
- “Show wines under €5.” — No matches (cheapest is €6.00); never invent a wine.
- “What is the price and stock of W-001?” — €8.50, 18 bottles.
- “A dry white for fish.” — Sweetness and food pairings are not recorded; the assistant
  must say so rather than guess.
- “Which wine is 13% alcohol?” — Alcohol is not recorded.
- “Prepare 99 bottles of W-001.” — Insufficient-stock guard.
- “Prepare one bottle of W-003.” — Out-of-stock guard (stock 0).

## Catalog facts

200 wines: 114 red, 68 white, 9 rosé, 4 dessert, 4 sparkling, 1 without a type.
37 are out of stock. 73 have no vintage. 68 have aroma tags the taster wrote; the rest have
only `taste_style_guess` (typical for the style, not tasted). 4 wines have no country.
Nine names appear twice (different vintages or listings); use the wine ID.
