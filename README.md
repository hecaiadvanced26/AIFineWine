# Wine retail assistant

A small course prototype: React UI, Python/Flask, the OpenAI client and SQLite.
Each file has one job. The catalog contains 200 imported wines with provenance-aware flavour notes;
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

Try: “Show Spanish reds under €15”, “Tell me about barcelino-tinto-2019-159331692”,
then “Prepare two bottles of barcelino-tinto-2019-159331692”. Review the exact draft and click **Confirm order**
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
| `database.py` | SQLite schema migration and imported catalog loading |
| `import_finewine.py` | Reproducible snapshot export from teammate SQLite and vocabulary |
| `refresh_demo_catalog.py` | Back up SQLite and replace catalog metadata, preserving historical orders |
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

## Imported teammate catalog

Source: [hecaiadvanced26/finewine](https://github.com/hecaiadvanced26/finewine),
commit `5df3f4d3262a38f189b85cb3696c6e30c2eafd22`. `data/catalog.json` is a
reproducible snapshot of the source's `wine_shop.sqlite` and `flavour_vocabulary.json`:
200 wines, 483 flavour records (133 stated, 350 inferred), and 88 vocabulary terms.
The repository omits the original `wines.json`; import uses its supplied SQLite
instead. Source code is not executed. Existing source IDs and unknown vintages
are preserved. Country codes `de` and `fr` normalize to Germany and France;
original values remain in the JSON attributes.

`wines` retains integer cents and stock for existing order code and adds explicit
producer, origin, regional style, type, bottle size, taster rating, community rating
and review columns. `flavours` stores each note with `stated` or `guess` provenance;
`flavour_vocabulary` supplies English/French labels, families and groups.
`prompts.py` describes these tables in both the system prompt and SQL tool.
Flavour search defaults to stated notes. Style guesses require customer agreement
and are explicitly labeled. Taster and community scores are separate imported
ratings, not independently verified reviews. Prices, stock and bottle sizes are
synthetic, seeded shop inventory, not real retail availability.

Grapes, dryness/sweetness, body, organic certification and food pairings are absent.
The assistant asks before ignoring these constraints; it must not infer them from
names, regions or fruit notes. Fruit notes describe aroma, not sweetness.

To import a later teammate revision:

```bash
git clone https://github.com/hecaiadvanced26/finewine.git /tmp/finewine
.venv/bin/python import_finewine.py /tmp/finewine
.venv/bin/python refresh_demo_catalog.py
```

Fresh databases seed from `data/catalog.json`. Existing databases need the refresh
command. It saves a SQLite backup before schema migration, replaces the four old
DEMO IDs with source IDs, updates metadata, and preserves remaining stock for
retained IDs. Historical order payloads remain unchanged, including references to
removed wines. Existing pending drafts for removed/changed items must be prepared
again. Repeated startup does not refill inventory or overwrite catalog metadata.
`data/demo_wines.json` is an unused legacy fixture.

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

## Vercel demo deployment

The linked Vercel project builds the React frontend into `public/` and runs
`server:app` as a Flask function. Set `OPENAI_API_KEY`, `OPENAI_MODEL`,
`OPENAI_BASE_URL`, and a random `FLASK_SECRET_KEY` in Vercel environment settings.
Set `WINE_DATA_DIR=/tmp/wine-retail-assistant` for writable demo storage.
The source catalog seeds each new runtime's database. `/api/health` checks the runtime.

This hosted version is a temporary demo: conversations live in process memory,
and stock changes and order exports live in temporary SQLite storage. They may
reset on restarts or differ between runtime instances. Order drafts can expire
between requests. Use a shared durable database and session store before treating
the deployment as a multi-user shop. No payment or real shop integration exists.

Deploy with `vercel --prod`. To roll back, promote a previous working deployment
from the Vercel project dashboard. Environment secrets remain outside Git.

## Manual checks

Offline catalog, order, API and status tests (no model calls; writes use temporary databases):

```bash
.venv/bin/python -m unittest -v test_catalog test_server test_status
```

Check a budget search, unknown wine ID, unsupported taste preference, insufficient
stock, cancellation and an order confirmation. In a fresh catalog, `20er-schulz-zweigelt-hagelsberg-nv-142492088` is out
of stock and must not appear in recommendations. Inspect the exported JSON after confirmation.

API/tool references: [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
and [Python SQLite](https://docs.python.org/3/library/sqlite3.html).
