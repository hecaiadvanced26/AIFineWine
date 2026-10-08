# Demo prompts

Run `./start.sh` and open http://localhost:8000. Real wine names, illustrative shop
prices, stock and ratings. No real payment, email or shop delivery integration.

## Main flow

1. “I want a fruity wine, not sweet, from Spain, to pair with chicken. Under €15.”
   Expected: Torres Sangre de Toro Original (€9.95) and Marqués de Riscal Verdejo
   (€12.95), subject to current stock. Fruity does not mean sweet.
2. “Only red, and I need two bottles.”
   Expected: Torres Sangre de Toro Original, provided at least two bottles remain.
3. “Prepare two bottles of DEMO-001.”
   Expected: draft totaling €19.90. No stock change until confirmation.
4. Click **Confirm order**.
   Expected: professional “Order confirmed” banner with name, quantity, total,
   vintage and expandable reference. Local export only; stock decreases by two.

Use **Cancel** for rehearsals without changing stock. Terminal equivalents:
`./start.sh --cli`, `/confirm`, `/cancel`.

## Other prompts

- “Show white wines from Rueda.” — Verdejo, if available.
- “A full-bodied Rioja red for lamb.” — Riscal Reserva (€22.95), if available.
- “Which wines have a shop rating of at least 4.2?” — Explain demo-score provenance.
- “Show wines under €5.” — No matches; never invent a wine.
- “What is the price and current stock of DEMO-002?” — Tool-backed factual lookup.
- “Prepare 99 bottles of DEMO-001.” — Insufficient-stock guard.
- “Prepare one bottle of DEMO-004.” — Out-of-stock guard.
- “Is it certified vegan?” — Not recorded; no guessing.

## Seed catalog

| ID | Wine | Type | Demo price | Vintage | Initial stock |
|---|---|---|---|---|---|
| DEMO-001 | Torres Sangre de Toro Original | Red | €9.95 | 2023 | 8 |
| DEMO-002 | Marqués de Riscal Verdejo | White | €12.95 | 2024 | 5 |
| DEMO-003 | Marqués de Riscal Reserva | Red | €22.95 | 2021 | 3 |
| DEMO-004 | Torres Viña Sol Original | White | €8.95 | 2024 | 0 |

Existing orders may have reduced stock. Refreshing catalog metadata keeps remaining
stock and old orders; it does not refill inventory.

## Explain to the teacher

The model sees the schema and attribute meanings, writes a SELECT query, then
calls the SQL tool. SQLite returns rows; the model uses those as answer context.
`json_extract` filters scalar facts; `json_each` checks food/grape arrays.
The last six turns support follow-ups. No separate Pydantic preference state or
extraction pass is needed. Exact wine ID and quantity are required only for orders.
Confirmation is application-side, never a model tool. Prices/vintage/stock are
checked again, and order IDs prevent duplicate stock deductions.
