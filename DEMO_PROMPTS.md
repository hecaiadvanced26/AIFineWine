# Demo prompts

Run `./start.sh` locally or open the Vercel demo. Catalog: 200 imported wines;
prices, inventory and bottle sizes are fictional. No real payment or delivery.
For an existing local database, first run `python refresh_demo_catalog.py`.

## Main flow

1. “Show red wines from Spain under €15. I need two bottles.”
   Expected: tool-backed available wines. Initial seed includes Barceliño Tinto
   (2019, €11.50, two bottles) and Félix Solís Los Molinos Gran Reserva (€7.50).
2. “Tell me about barcelino-tinto-2019-159331692, including flavour provenance.”
   Expected: imported metadata; any style guesses labeled inferred.
3. “Prepare two bottles of barcelino-tinto-2019-159331692.”
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
- “Prepare 99 bottles of barcelino-tinto-2019-159331692.” — Stock guard.
- “Prepare one bottle of 20er-schulz-zweigelt-hagelsberg-nv-142492088.” —
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
