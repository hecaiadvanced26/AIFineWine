# Wine retail assistant

A small course prototype: React UI, Python/Flask, the OpenAI client (pointed at OpenRouter) and SQLite.
The shop is **fictional**: cave. (always written lowercase with the full stop). The catalogue holds 250 invented wines.
Countries, regions, appellations and grape varieties are meant to be real (see "Fictional catalogue" below);
producers, cuvée names, vintages, prices, stock, ratings and the 75 tasting notes are invented.
Orders are exported locally and are not sent to a real shop.

Hosted demo: [advanced-ai-systems.vercel.app](https://advanced-ai-systems.vercel.app).
Its chat and inventory storage are temporary; see the limitations below.

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

Try: “Show Spanish reds under €15”, “Tell me about W-015”,
then “Prepare two bottles of W-015”. Review the exact draft and click **Confirm order**
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
| `make_hec_catalog.py`, `hec_catalog_data.py` | Deterministic generator and validator of the fictional 250-wine catalogue (`data/catalog.json`, `data/catalog_overview.csv`) |
| `import_finewine.py` | LEGACY: snapshot export from the old teammate SQLite; not used for the current catalogue |
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
uses the rows to answer the customer. SQLite errors return to the model for
correction within the turn's tool budget. Queries use a read-only connection and
must start with `SELECT`. The prompt requests at most five recommendations.

## Query execution: SQL tool, not a code sandbox

The model receives the actual schema and field descriptions in `prompts.py`, then
supplies SQL as the argument to `run_query`. `catalog.py` opens a SQLite connection
with `mode=ro`, runs one statement through `sqlite3.execute`, returns rows, and
closes the connection. Queries execute inside the Flask/Python process.

We did not implement an isolated sandbox for model-generated Python or shell
code. The model can call two predefined tools: `run_query` and `prepare_order`.
It cannot execute arbitrary Python, launch shell commands, or invoke
`submit_order`; confirmation and database writes belong to application code.
The read-only SQLite connection is a database permission boundary, not a separate
process/container sandbox.

The teammate's agent uses structured `search_wines` filters and constructs SQL
in Python. We imported its data, not its agent implementation. Our assistant
retains model-written SQL so it can combine the documented columns and flavour
tables without adding a separate search function for every preference.

| Design choice | Current implementation | Trade-off |
|---|---|---|
| Database search | Model-generated `SELECT` executed by a predefined backend tool | Flexible queries, but correctness depends on the model and schema descriptions |
| Code execution | No arbitrary Python/shell execution and no isolated code sandbox | Small implementation; SQL still runs in the application process |
| Query restrictions | Read-only connection, `SELECT` prefix check, one statement, up to ten returned rows | No table allowlist, SQL cost limit, or query execution timeout |
| Preference tracking | Recent messages rather than a dedicated preference object | Simple follow-ups, but constraints can be lost or misinterpreted |
| Order submission | One-item draft plus an explicit UI/CLI confirmation | No multi-item checkout, payment, delivery, or real shop integration |

A ten-row response cap limits returned data, not query work: a large scan or
expensive join can still consume resources. The SQL tool is not restricted to
catalog tables; other tables in the same database, including local order history,
are readable. There is no database authorizer or per-customer row access policy.
These are limits of this course prototype, not guarantees of production isolation.

## Fictional catalogue (250 wines)

Regenerate with `python make_hec_catalog.py` (seed 20261009, output is identical each run). It writes
`data/catalog.json` and `data/catalog_overview.csv` (open the CSV to spot-check every wine).
Reading the generator: `hec_catalog_data.py` holds the templates, `data/tasting_notes.json` the 75 notes.

- **Mix:** 120 red, 85 white, 28 sparkling, 17 rosé; many countries, regions, appellations and grapes.
- **Real (intended):** country, region, appellation and the grape blend of each appellation/style. Source: the
  two PDFs supplied by the team (a restaurant wine list, GuildSomm grape profiles) plus the author's general
  wine knowledge. **Not independently verified**: have a wine-knowledgeable teammate scan the CSV.
- **Invented:** producer names, cuvées, vintages, prices, stock (some wines are at 0), community ratings and
  tasting notes. Producer names may coincide with real estates by accident.
- **Same producer, three vintages:** 9 cuvées exist in three vintages with different price, rating and stock
  (test whether the assistant separates them, e.g. "Which Domaine des Grands Champs Les Silex vintage is best?").
- **Tasting notes:** exactly 75 wines have an invented personal note; its aroma words are the `stated`
  flavour tags (200 stated tags in total). All other aromas are `guess` (typical for the style).
- **Profile per wine:** sweetness, body, acidity, tannin (reds only), fruitiness on a 1-5 scale, and food
  pairings (35 tags). These are *demo profiles typical for the grape and style, not measured per bottle*.
  Ranges for 12 grapes follow the GuildSomm profiles; ranges for other grapes and all food pairings are the
  author's estimates.
- **Not recorded:** organic certification, alcohol level, occasion. The assistant must say so.

Tables: `wines` (incl. profile columns, `inventory_synthetic`), `wine_grapes`, `wine_pairings`, `flavours`
(`stated`/`guess`), `flavour_vocabulary` (88 terms), `catalog_metadata`, `orders`.
Fresh databases seed from `data/catalog.json` only when `wines` is empty. **An existing local database keeps the
old wines: delete `data/wines.db` (or run `python refresh_demo_catalog.py`) after pulling this version.**
On Vercel the database is rebuilt on a cold start.

## Security guardrails

Principle from the course: the trust boundary lives in code you own, not in the prompt. Layers, in order:

| Layer | Where | What it stops |
|---|---|---|
| Input screen | `guard.screen_input`, `server.py` | Known override phrasings ("ignore previous instructions", "show your system prompt", fake system tags, "I am the supervisor/admin"), and valid card numbers (Luhn check). The message never reaches the model and is not stored. |
| Rate limits | `server.py` | 15 chat requests per minute per client, 80 turns per conversation, 4,000 characters per message, `max_tokens=700` per model call, 4 steps and 6 tool calls per turn. |
| SQL tool | `catalog.py` | Authorizer allows SELECT only on `wines`, `flavours`, `flavour_vocabulary`, `wine_grapes`, `wine_pairings`: no `orders`, `catalog_metadata`, `sqlite_master`, PRAGMA, ATTACH or extensions. `stock` is never returned by this tool (the cards show "n in stock" to customers by design, and the card tools pass `stock` to the model). Runaway joins are aborted. The connection is read-only. |
| Tool arguments | `tools.py`, `orders.py` | `prepare_order` takes only wine ID and quantity. Price and total come from the database, quantity is 1 to 12 and at most the stock. Confirmation is a button in the page, not a model tool. |
| One output per turn | `tools.py` | A turn shows a question or one set of results, never both. |
| Output screen | `guard.reply_problem`, `agent.py`, `server.py` | Replies with the canary marker, tool or table names, SQL, card numbers, key names, unknown email addresses, or discount/coupon/free-bottle claims are replaced by a safe message and not stored. Streamed text stops as soon as it breaks a rule. |
| Prompt | `prompts.py` "Security rules" | Customer text and tool results are data; no discounts, no special roles; no internal topics. This layer is the weakest: it is a request to the model, not a guarantee. |

Tests: `python -m unittest test_guard` (17 offline tests; each guard was also checked by switching it off and
watching a test fail). Live check with the real model: `python redteam_run.py URL` (see `DEMO_PROMPTS.md`).

Known limits: (1) pattern lists catch known wordings only; paraphrases, other languages and multi-turn tricks rely on the
prompt and the code layers behind it. (2) The order total shown on the card is always right, but the model's *sentence*
could still be wrong; the output screen only catches typical discount wording. (3) Rate limits and turn counters
live in memory, so on Vercel they are per instance and can be sidestepped. There is no login or spend cap on the public
URL. (4) A reply that streams a few words before breaking a rule is cut off, not recalled. (5) A withheld reply also clears the cards of that turn. (6) The page shows blocked messages as normal chat replies. (7) Prompt-injection through data would need
someone to change `data/catalog.json`; the catalogue is trusted content.

## Prototype limitations

- **Data coverage:** structure and pairings are typical-for-style estimates, not per-bottle measurements;
  certifications, alcohol and occasion are not recorded. Only 3 wines are sweet and 10 off-dry.
- **Data provenance:** everything commercial is invented. Of 1028 flavour records, 828 are style guesses and
  200 come from the 75 invented notes. Real/invented accuracy of appellations and grapes is unverified.
- **Model reliability:** prompt rules request grounding, stated-note matching
  and permission before relaxing constraints, but do not mechanically validate
  every SQL filter or sentence in the final reply. Model/tool errors remain possible.
- **Bounded conversation:** each turn allows four model steps and six tool-call
  attempts; later attempts can receive budget errors instead of executing. Only
  six recent turns are retained, with no summary or durable preference state.
- **Hosted persistence:** Vercel uses process memory for chats and `/tmp` SQLite
  for inventory/orders. Restarts can reset them; different instances can have
  different stock and missing drafts. Duplicate-order protection applies within
  one database, not across independent instances.
- **Shop scope:** one wine per draft, local JSON export, no customer account,
  delivery, payment, email confirmation, or external order acceptance.

A durable multi-user version would need shared inventory/order storage, a shared
session store, customer access controls, and stronger query execution restrictions.

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

The homepage is served with `Cache-Control: no-store` and conditional file
responses disabled. This avoids stale HTML referencing a removed JavaScript
bundle when Vercel build files share the same timestamp and size. If a browser
still shows an old blank page, perform a hard refresh once.

## Manual checks

Offline catalog, order, API and status tests (no model calls; writes use temporary databases):

```bash
.venv/bin/python -m unittest -v test_catalog test_server test_status
```

Check a budget search, unknown wine ID, unsupported taste preference, insufficient
stock, cancellation and an order confirmation. In a fresh catalog, `W-003` is out
of stock and must not appear in recommendations. Inspect the exported JSON after confirmation.

API/tool references: [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
and [Python SQLite](https://docs.python.org/3/library/sqlite3.html).


## Guided advice

`advisor.py` adds three tools next to `run_query` and `prepare_order`: `recommend_wines` (colour and
budget filter; profile, grapes, foods, aromas, country and region rank; at most 3 wines), `find_cheaper_alternatives` (same colour,
cheaper, shared aroma tags) and `offer_choices` (quick-reply chips with a step counter). The model
proposes a profile; the code filters, ranks and returns only catalog facts. The page shows the
results as cards (`frontend/src/Advisor.jsx`). The code also matches sweetness, body, acidity, tannin, fruitiness, grapes (incl. synonyms such as
Shiraz), food pairings and region. Occasion is not recorded; the prompt tells the model to say so.
Tests: `python -m unittest test_advisor`.

**Scores on the cards.** Stars show the public community rating (`community_avg_rating`, out of 5; partial
stars are drawn). Wine glasses show the *fit with the customer's wishes*: the share of wishes met, scaled to
1-5 (`fit_score` in `advisor.py`; 5 = all wishes met). Colour and budget count as wishes. Cards are ranked
#1-#3 by wishes met, then taster-stated aroma hits, then taster rating, then lower price.

**Bottle images.** `make_wine_images.py` (from the team) draws a bottle per wine as SVG: colour by wine type,
label text from the name, winery and vintage (no year if unknown). The server serves them at
`/api/wine-image/<wine_id>.svg`, so nothing is stored. They are illustrations, not product photos.
`python make_wine_images.py` still writes static files if you want them.

**Quantity.** Cards and the order draft have a − / + selector from 1 up to the wine's stock. Changing it on the draft
calls `POST /api/order` with `action: "quantity"`; the server rebuilds the draft from the database (price, stock),
issues a new `order_id` and refuses 0, negatives, non-integers and anything above stock. Stock only changes on Confirm.
Tests: `python -m unittest test_quantity`.

**Name.** The shop is called cave. (with the full stop); the assistant has no personal name. The favicon is `frontend/public/favicon.svg`, linked in `frontend/index.html`.

**Text only.** The chat cannot receive photos, label scans or files. `prompts.py` (section "What this chat can do") forbids asking for them and answers requests with "planned for a future update".

**Assistant instructions.** `prompts.py` holds the permanent role (`PERSONA`: voice, opening message, how to find wines,
staying on topic, orders and staff topics, never-discuss list, responsible service, format), then `DATA_RULES` (what the
catalog does and does not record) and `GUIDED_ADVICE` (tools and chips), then the schema. `STAFF_EMAIL` is the same address as `CONTACT_EMAIL` in `App.jsx` (`jan.laufing@hec.edu`, a real
mailbox; `test_prompts.py` checks that they match). Tests: `python -m unittest test_prompts`.
