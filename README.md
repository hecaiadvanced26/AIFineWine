# Wine retail assistant

A small course prototype: React UI, Python/Flask, the OpenAI client and SQLite.
Each file has one job. The catalog contains four real wine names with demo shop data;
orders are exported locally and are not sent to a real shop.

## Run

See [DEMO_PROMPTS.md](DEMO_PROMPTS.md) for a ready-to-use demonstration conversation.

From this folder:

```bash
./start.sh
```

The script loads `.env`, creates `.venv` if needed, installs the dependency and
builds React and starts the browser chat at http://localhost:8000. Node.js 20.19+
or 22.12+ is required. The local `.env` is configured for `gpt-5-mini` with
OpenAI. It is ignored by Git; `.env.example` contains shareable placeholders.
On another machine, copy `.env.example` to `.env` and enter your own key.
For the original terminal demo, run `./start.sh --cli`.

The browser shows live reply text and real activity: contacting the model,
preparing a tool request, querying the catalog, and preparing an order.
Open “View activity” to see the events. Status changes come from callbacks
at those operations, not timers. Each browser session has separate conversation
memory; all sessions share the shop catalog and stock. Reloading starts a fresh
conversation. This is a local demo, not a deployed multi-user service.

React sends a message to Flask. Flask calls the existing agent, and streams JSON
lines containing `status`, `text`, and `done` events. React displays those events.
The API key and order draft remain on the Python server, never in frontend code.

For OpenRouter, change `OPENAI_BASE_URL` in `.env` to
`https://openrouter.ai/api/v1` and use an OpenRouter model ID. Provider/model must
support chat tool calls.

Assistant replies appear as text fragments arrive. SQL tool arguments are collected
until the stream finishes, then executed. The complete reply is saved in chat memory.

Try: “Show available wines under €20”, “Tell me about DEMO-001”, then
“Prepare two bottles of DEMO-001”. Review the exact draft and click **Confirm order**
or **Cancel order**. In the terminal, type `/confirm` instead.
Use `/cancel` to discard it and `/quit` to exit. Any other chat message discards a
pending draft so a changed request cannot accidentally confirm the old order.

## Files

| File | Responsibility |
|---|---|
| `frontend/src/App.jsx` | React chat, streamed replies and live activity |
| `frontend/src/OrderCard.jsx` | Order review and explicit confirmation buttons |
| `frontend/src/OrderConfirmation.jsx` | Professional confirmation banner and receipt summary |
| `frontend/src/api.js` | Fetch requests and streamed JSON-line decoding |
| `server.py` | Flask bridge, session memory, stream events and order endpoints |
| `main.py` | Terminal input, output and explicit order confirmation |
| `agent.py` | At most four model steps and six tool executions per turn |
| `streaming.py` | Display reply fragments and collect complete streamed tool calls |
| `prompts.py` | System instructions and database/attribute descriptions |
| `tools.py` | Two tool definitions and function dispatch |
| `catalog.py` | Execute model-written SELECT queries; look up order items |
| `orders.py` | Order drafts, stock/price checks and duplicate prevention |
| `database.py` | SQLite setup and initial demo data loading |
| `memory.py` | Last six complete turns and pending order state |

Money is stored as integer cents. Each wine ID represents one sellable vintage.
`null` vintage means unknown/non-vintage; the assistant must not guess which.
The model writes SQL using the schema in the tool description. For example:

```sql
SELECT wine_id, name, price_cents, vintage, stock
FROM wines
WHERE stock > 0 AND price_cents <= 2000
ORDER BY price_cents LIMIT 5;
```

`run_query(sql)` executes that SQL with SQLite and returns up to ten rows. The model
uses the rows to answer the customer. SQLite errors return to the model for one
correction attempt. Queries use a read-only connection and must start with SELECT.

## Add the teammate's data

`ATTRIBUTE_DESCRIPTIONS` in `prompts.py` documents the populated JSON fields:
brand, type, country, region, grapes, sweetness, fruitiness, body, tasting notes,
pairings, rating and bottle size. The same description appears in the system
prompt and SQL tool. Scalars use `json_extract`; array membership uses `json_each`.
Fruitiness is independent of sweetness. Missing preferences impose no filter.
Update these descriptions when the teammate supplies the final catalog.

Names/origins/grapes are based on producer references:
[Torres Sangre de Toro](https://www.torres.es/en/wines/torres-essentials/sangre-de-toro-original),
[Riscal Verdejo](https://www.marquesderiscal.com/marques-de-riscal-verdejo),
[Riscal Reserva](https://www.marquesderiscal.com/marques-de-riscal-reserva),
[Torres Viña Sol](https://www.torres.es/en/wines/torres-essentials/vina-sol-original).
Prices, stock, vintage assignments and ratings are illustrative, not verified live
retail data. Taste/body/sweetness classifications and food tags are demo shop
annotations, not producer-certified vintage profiles. Ratings are synthetic demo
shop scores, not claims about critic scores or customer reviews.

Replace `data/demo_wines.json` with the agreed catalog before first initialization.
It loads only when the wine table is empty; changing the JSON does not overwrite an
existing database. A catalog import/update script can be added once its format is known.
Update the prompt's demo wording when real data is loaded.
To update the four existing demo items, run `.venv/bin/python refresh_demo_catalog.py`.
This backs up SQLite and changes names/prices/vintages/attributes, preserving current
stock, wine IDs and historical orders. It does not run automatically at startup.

## Orders and memory

`prepare_order` creates a single-item draft. `/confirm` exports that exact draft.
Prices, vintage and stock are rechecked; changed data requires a new draft.
Orders are saved in SQLite and `data/orders/<order_id>.json`. Repeating the same ID
does not decrement stock twice. This is a local shop-system placeholder: no customer
details, delivery, payment or real shop integration are included yet.

Recent history keeps whole turns, including tool messages. Older turns are dropped;
compression and FAQ retrieval remain optional future additions. Search preferences
are optional: missing preferences mean no filter, and 'any'/'no limit' remove a
constraint. A complete preference form or Pydantic model is not required. Stock and price
always come from tools, not chat memory.

## Manual checks

Offline UI and status tests (no API calls or database writes):

```bash
.venv/bin/python -m unittest -v test_catalog test_server test_status
```

Check a budget search, unknown wine ID, unsupported taste preference, insufficient
stock, cancellation and an order confirmation. In a fresh catalog, DEMO-004 is out
of stock and must not appear in search. Inspect the exported JSON after confirmation.

API/tool references: [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
and [Python SQLite](https://docs.python.org/3/library/sqlite3.html).
