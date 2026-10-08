# Demo prompts

Run `./start.sh` locally or open the Vercel demo. Catalog: 200 imported wines;
prices, inventory and bottle sizes are fictional. No real payment or delivery.
For an existing local database, first run `python refresh_demo_catalog.py`.

## Main flow

1. “Show red wines from Spain under €15. I need two bottles.”
   Expected: tool-backed available wines. Initial seed includes Barceliño Tinto
   (2019, €11.50, two bottles) and Félix Solís Los Molinos Gran Reserva (€7.50).
2. “Tell me about W-015, including flavour provenance.”
   Expected: imported metadata; any style guesses labeled inferred.
3. “Prepare two bottles of W-015.”
   Expected: €23.00 draft; stock unchanged before confirmation.
4. Click **Confirm order** or use `/confirm` in the terminal.
   Expected: local demo export; stock decreases once. Repeating the same order ID
   does not deduct stock again. Use **Cancel** for rehearsals.

## Provenance and missing-field checks

- “Red wines with stated blackberry notes under €20.” — Match stated notes only;
  initial seed includes 8 Bagatella Zinfandel.
- “Include style-based flavour guesses too.” — May include inferred notes,
  clearly labeled as guesses.
- “Fruity, dry wine for chicken.” — Explain dryness and pairings are not recorded;
  ask before ignoring unsupported constraints. Fruitiness is aroma, not sweetness.
- “Compare taster ratings with community ratings.” — Separate score columns;
  missing values remain unknown. Never call these verified shop ratings.
- “What vintage is a wine whose vintage is NULL?” — Unknown/non-vintage;
  never infer a year from its ID or name.
- “Show wines under €5.” — Query first; no invented match.
- “Prepare 99 bottles of W-015.” — Stock guard.
- “Prepare one bottle of W-003.” —
  Out-of-stock guard in fresh seed.
- “Certified organic wines?” — Certification not recorded, even if a name says Bio.

## Explain to the teacher

The model writes a SELECT from the schema shared by system prompt and SQL tool.
Explicit wine columns support origin/type/budget/rating filters; `EXISTS` against
`flavours` checks notes without duplicate wines. Vocabulary families group fruit
aromas and citrus notes. `provenance='stated'` separates tasting notes from guesses.

Source revision and inventory caveats are bundled in `data/catalog.json`.
SQLite migrations back up old data and preserve order history and retained stock.
Confirmation is application-side, not a model tool. Orders recheck price, vintage
and stock. Vercel storage remains temporary; drafts may expire between instances.

## Guided advice (new)

Not yet run against a real model; check each step on the live site and note what differs.

1. “Help me choose a wine.” Expected: the assistant asks ONE question (colour) and shows chips
   with “Question 1 of 4”. Tap **Red**, then a budget chip such as **€8–12**, then an aroma chip
   such as **Red berries & cherry**.
2. Expected: up to 3 wine cards (price, ratings, “Fits n of m of your wishes”, aromas split into
   “the taster wrote” and “typical for this style, not tasted”), plus one plain-language sentence
   per wine. Aroma matches use taster-written notes only unless you agree to style guesses.
3. Click **Cheaper alternative** on a card. Expected: your wine next to up to 2 cheaper wines of the
   same colour that share aroma tags, with the price difference. The assistant must NOT say they taste the same.
4. “It's for a barbecue and I like it dry.” Expected: the assistant says occasion, food and sweetness
   are not recorded and continues with colour, budget and aromas.
5. Click **Choose this wine**. Expected: the usual order draft, then **Confirm order**.

## Quantity (new)

Not yet run against a real model. On a card, set the selector to 3 and click **Choose this wine**: the draft should show
3 bottles and the total. Change the draft's selector to 2: total updates, stock stays unchanged until **Confirm order**.
Try to go above the stock: the + button stops at the stock. Typing 99 in the box is clamped to the stock.
