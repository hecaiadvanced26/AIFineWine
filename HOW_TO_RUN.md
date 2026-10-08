# How to run cave. (step by step)

Written for a team member who has the project folder and an API key. Windows commands are given where they differ.
I could not run the web page or the real model in my build environment, so treat the first real run as the test of
these steps and tell us where they are wrong.

## 0. What you need
- Python 3.11 or newer recommended (the tests ran with 3.13; older versions are untested), pip.
- Node.js 20.19+ or 22.12+ (needed only for the web page, not for the tests or the terminal version).
- An OpenRouter account and key: openrouter.ai, "Keys". Add a few dollars of credit for the evaluation.
- The project folder (the unzipped repository). All commands below start inside it.

## 1. Settings (once)
1. Copy `.env.example` to a new file called `.env` (a hidden file; on Windows use `copy .env.example .env`).
2. Put these three lines in it, with your own values:
   ```
   OPENAI_API_KEY='your OpenRouter key'
   OPENAI_MODEL='vendor/model-name'
   OPENAI_BASE_URL='https://openrouter.ai/api/v1'
   ```
   The model name is the ID shown on the model's OpenRouter page. It must support tool calling.
   (The variable names are still the OpenAI ones; they will be renamed to OpenRouter names in a later step.)
3. Never commit `.env` or paste the key into chat or files. `.gitignore` already excludes it.

## 2. Install (once)
Mac or Linux:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Windows (PowerShell):
```
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Load the settings into the terminal. Mac/Linux: `set -a; source .env; set +a`. Windows PowerShell: set each one,
e.g. `$env:OPENAI_API_KEY="..."; $env:OPENAI_MODEL="..."; $env:OPENAI_BASE_URL="https://openrouter.ai/api/v1"`.

## 3. Check that nothing is broken (no key needed, no cost)
```
python -m unittest
```
Expected: `OK`, around 99 tests. If a test fails, stop and tell us which one.

## 4. Run the web page
Mac/Linux: `./start.sh` (it loads `.env`, installs, builds the page, starts the server).
Windows or manual:
```
cd frontend
npm install
npm run build
cd ..
python server.py
```
Open http://localhost:8000. The local database is created at the first start in `data/wines.db`. After the catalogue
file changes, delete `data/wines.db` and start again. The terminal version is `python main.py`.

## 5. Look at costs and speed
Every model call writes one line (token counts, cost if the provider reports it, latency, never the message text) to
`data/usage_log.jsonl` and to the server output as `USAGE {...}`. After some chatting:
```
python cost_report.py
python cost_report.py --price-in 0.25 --price-out 2 data/usage_log.jsonl    # prices in USD per 1M tokens, from the model page
```
On Vercel the lines are in the project's Logs; export them to a file and use `--from-vercel-logs export.txt`.
The numbers in the example above are placeholders for the command format, not real prices.

## 6. Security check (costs a few cents)
```
python redteam_run.py http://localhost:8000
python redteam_run.py https://ai-fine-wine.vercel.app
```
Read every reply. `REVIEW` means a rule was visibly broken; `PASS` does not prove safety.

## 7. Measured results (see TEAM_TASKS.md)
```
python eval_run.py --check                       # validate the questions, free
python eval_run.py --runs 1 --label test         # one pass: note time and cost
python eval_run.py --runs 3 --label modelA --out results_modelA.jsonl
python eval_run.py --summarize results_modelA.jsonl results_modelB.jsonl
```
The runner uses its own temporary database, so orders and stock in your local app are untouched.

## Common problems
- "Set OPENAI_API_KEY and OPENAI_MODEL first": step 2 was not done in this terminal window.
- "Model reply failed or was interrupted": wrong model name, no credit, or a model without tool support. The usage log
  line for that call has `"error"`.
- Port 8000 busy: close the other server first.
- The page shows the old wines: delete `data/wines.db`.
- Replies stop early with a very short answer: raise `MAX_OUTPUT_TOKENS` (default 2000) in the settings.
