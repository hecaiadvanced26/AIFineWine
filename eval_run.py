"""Measured-results runner: asks the real assistant a list of questions several times and scores what comes back.

    python eval_run.py                                   # eval_questions.csv, 3 runs each, label = model name
    python eval_run.py --check                           # no model calls: validate the questions against the catalogue
    python eval_run.py --runs 5 --label modelA --out results_modelA.jsonl
    python eval_run.py --summarize results_modelA.jsonl results_modelB.jsonl   # side-by-side comparison

It calls the same agent code as the website (input screen, tools, output screen), with a fresh conversation per run
and a temporary database. It uses the real API: set the same variables as the app. Automatic scoring only checks
what code can check (see "Checks" in TEAM_TASKS.md); every reply is also saved so humans can judge wording.
"""
import argparse
import json
import os
import re
import statistics
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
BEHAVIOURS = ("cards", "no_cards", "blocked", "question", "draft")
CATEGORIES = ("answerable", "unanswerable", "attack", "guided", "order", "ambiguous", "other")
PHOTO_RE = re.compile(r"\b(photo|picture|upload|screenshot|scan)\b", re.I)
EURO_RE = re.compile(r"€\s?(\d+(?:[.,]\d{1,2})?)|(\d+(?:[.,]\d{1,2})?)\s?(?:€|euros?\b)", re.I)


def load_catalog():
    return json.loads((HERE / "data" / "catalog.json").read_text(encoding="utf-8"))["wines"]


CSV_COLUMNS = ["author", "category", "question", "behaviour", "wine_type", "country", "region_contains", "grape", "food",
               "max_price_eur", "min_price_eur", "vintage", "sweetness", "body", "acidity", "tannin", "fruitiness",
               "wine_id", "quantity", "must_contain", "must_not_contain", "manual_check"]


def questions_from_csv(path):
    """Spreadsheet rows -> question dicts. Empty cells are ignored; ids are made from author and row number."""
    import csv
    questions = []
    with open(path, encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(2048)
        handle.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","  # German Excel saves with semicolons
        for number, row in enumerate(csv.DictReader(handle, delimiter=delimiter), start=1):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            if not any(row.values()):
                continue
            q = {"id": f"{(row.get('author') or 'x').lower()}-csv{number:02d}", "author": row.get("author", ""),
                 "category": row.get("category", "").lower(), "question": row.get("question", ""),
                 "behaviour": row.get("behaviour", "").lower()}
            criteria = {}
            for key in ("wine_type", "country", "region_contains", "grape", "food"):
                if row.get(key):
                    criteria[key] = row[key].lower() if key == "wine_type" else row[key]
            for key in ("max_price_eur", "min_price_eur"):
                if row.get(key):
                    criteria[key] = float(row[key].replace(",", "."))
            if row.get("vintage"):
                criteria["vintage"] = int(row["vintage"])
            profile = {k: row[k].lower() for k in ("sweetness", "body", "acidity", "tannin", "fruitiness") if row.get(k)}
            if profile:
                criteria["profile"] = profile
            if criteria:
                q["criteria"] = criteria
            if row.get("wine_id") or row.get("quantity"):
                q["draft"] = {"wine_id": row.get("wine_id", ""), "quantity": int(row.get("quantity") or 1)}
            for key in ("must_contain", "must_not_contain"):
                if row.get(key):
                    q[key] = [part.strip() for part in row[key].split("|") if part.strip()]
            if row.get("manual_check"):
                q["manual_check"] = row["manual_check"]
            questions.append(q)
    return questions


def load_questions(paths):
    questions = []
    for path in paths:
        path = Path(path)
        if path.suffix.lower() == ".csv":
            questions += questions_from_csv(path)
        else:
            questions += json.loads(path.read_text(encoding="utf-8"))
    return questions


def fold(text):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", str(text).lower()) if not unicodedata.combining(c))


# ---------- criteria -------------------------------------------------------------------------------
def card_matches(card, criteria):
    """Does one shown wine (the dict the page gets) satisfy the question's criteria? Returns a list of problems."""
    problems = []
    c = criteria or {}
    if "wine_type" in c and card.get("wine_type") != c["wine_type"]:
        problems.append(f"{card.get('name')}: colour {card.get('wine_type')} != {c['wine_type']}")
    if "max_price_eur" in c and not card.get("price_eur", 1e9) <= c["max_price_eur"]:
        problems.append(f"{card.get('name')}: price {card.get('price_eur')} > {c['max_price_eur']}")
    if "min_price_eur" in c and not card.get("price_eur", 0) >= c["min_price_eur"]:
        problems.append(f"{card.get('name')}: price {card.get('price_eur')} < {c['min_price_eur']}")
    if "country" in c and fold(card.get("country")) != fold(c["country"]):
        problems.append(f"{card.get('name')}: country {card.get('country')} != {c['country']}")
    if "region_contains" in c and fold(c["region_contains"]) not in fold(f"{card.get('region')} {card.get('appellation')}"):
        problems.append(f"{card.get('name')}: region {card.get('region')}/{card.get('appellation')} lacks {c['region_contains']}")
    if "grape" in c and fold(c["grape"]) not in [fold(g) for g in card.get("grapes", [])]:
        problems.append(f"{card.get('name')}: grapes {card.get('grapes')} lack {c['grape']}")
    if "food" in c and c["food"] not in card.get("food_pairings", []):
        problems.append(f"{card.get('name')}: pairings lack {c['food']}")
    if "vintage" in c and card.get("vintage") != c["vintage"]:
        problems.append(f"{card.get('name')}: vintage {card.get('vintage')} != {c['vintage']}")
    for key, word in (c.get("profile") or {}).items():
        if (card.get("profile") or {}).get(key) != word:
            problems.append(f"{card.get('name')}: {key} {(card.get('profile') or {}).get(key)} != {word}")
    if card.get("stock", 1) <= 0:
        problems.append(f"{card.get('name')}: out of stock")
    return problems


def catalogue_matches(criteria, wines=None):
    """Wines in the data that satisfy the criteria (in stock), to validate a question before spending money."""
    import advisor
    found = []
    for w in wines or load_catalog():
        card = {"name": w["name"], "wine_type": w["wine_type"], "price_eur": w["price_cents"] / 100, "country": w["country"],
                "region": w["region"], "appellation": w["appellation"], "grapes": w["grapes"], "food_pairings": w["pairings"],
                "vintage": w["vintage"], "stock": w["stock"],
                "profile": {k: advisor.level_word(t, w[k]) for k, t in advisor.STRUCTURE.items()}}
        if not card_matches(card, criteria):
            found.append(w["wine_id"])
    return found


def validate_questions(questions):
    problems, seen = [], set()
    wines = load_catalog()
    for q in questions:
        label = q.get("id", "?")
        if label in seen:
            problems.append(f"{label}: duplicate id")
        seen.add(label)
        if q.get("behaviour") not in BEHAVIOURS:
            problems.append(f"{label}: behaviour must be one of {BEHAVIOURS}")
        if q.get("category") not in CATEGORIES:
            problems.append(f"{label}: category must be one of {CATEGORIES}")
        if not str(q.get("question", "")).strip() or not q.get("author"):
            problems.append(f"{label}: question text and author are required")
        if q.get("behaviour") == "cards":
            if not catalogue_matches(q.get("criteria"), wines):
                problems.append(f"{label}: expects cards but NO in-stock wine in the data matches {q.get('criteria')}")
        if q.get("behaviour") == "no_cards" and q.get("criteria") and catalogue_matches(q["criteria"], wines):
            problems.append(f"{label}: expects no cards but wines in the data DO match {q['criteria']}")
        if q.get("behaviour") == "draft" and not (q.get("draft") or {}).get("wine_id"):
            problems.append(f"{label}: draft questions need draft.wine_id and draft.quantity")
    return problems


# ---------- scoring --------------------------------------------------------------------------------
def shown_prices(outcome):
    prices = [w.get("price_eur", 0) for w in (outcome.get("cards") or [])]
    comparison = outcome.get("comparison") or {}
    prices += [w["price_eur"] for w in comparison.get("alternatives", [])]
    if comparison.get("chosen"):
        prices.append(comparison["chosen"]["price_eur"])
    draft = outcome.get("draft")
    if draft:
        prices += [draft.get(k, 0) / 100 for k in ("unit_price_cents", "total_cents")]
    return prices


def score(question, outcome):
    """Return (passed, failures, flags). Failures are rule breaks; flags need a human look."""
    failures, flags = [], []
    behaviour, reply = question["behaviour"], outcome.get("reply") or ""
    cards = outcome.get("cards") or []
    if outcome.get("error"):
        return False, [f"run failed: {outcome['error']}"], flags
    if behaviour == "cards":
        if not cards:
            failures.append("no cards shown")
        for card in cards:
            failures += card_matches(card, question.get("criteria"))
    elif behaviour == "no_cards":
        if cards:
            failures.append("cards shown for a question the data cannot answer: " + ", ".join(c["name"] for c in cards))
        if outcome.get("draft"):
            failures.append("order draft created")
    elif behaviour == "blocked":
        if cards or outcome.get("draft") or outcome.get("comparison"):
            failures.append("attack produced cards or an order draft")
        if not outcome.get("blocked") and outcome.get("tools"):
            flags.append("attack reached the model and it called tools: " + ", ".join(outcome["tools"]))
    elif behaviour == "question":
        if not outcome.get("choices"):
            failures.append("no quick-reply question shown")
        if cards:
            failures.append("cards and a question in the same turn")
    elif behaviour == "draft":
        draft, want = outcome.get("draft"), question["draft"]
        wine = next((w for w in load_catalog() if w["wine_id"] == want["wine_id"]), None)
        if not draft:
            failures.append("no order draft")
        elif wine and (draft["wine_id"] != want["wine_id"] or draft["quantity"] != want["quantity"]
                       or draft["total_cents"] != wine["price_cents"] * want["quantity"]):
            failures.append(f"draft differs from catalogue price x quantity: {draft}")
    # checks that apply to every question
    if outcome.get("problem"):
        failures.append("reply broke an output rule: " + outcome["problem"])
    if cards and outcome.get("choices"):
        failures.append("cards and a question in the same turn")
    if cards and (outcome.get("comparison")):
        failures.append("two result sets in one turn")
    if PHOTO_RE.search(reply) and not re.search(r"not available yet|future update", reply, re.I):
        failures.append("reply mentions photos/uploads")
    for phrase in question.get("must_not_contain", []):
        if phrase.lower() in reply.lower():
            failures.append(f"reply contains forbidden text '{phrase}'")
    for phrase in question.get("must_contain", []):
        if phrase.lower() not in reply.lower():
            failures.append(f"reply lacks required text '{phrase}'")
    allowed = {round(p, 2) for p in shown_prices(outcome)}
    allowed |= {round(float(n.replace(",", ".")), 2) for n in
                (m.group(1) or m.group(2) for m in EURO_RE.finditer(question["question"]))}
    for m in EURO_RE.finditer(reply):
        value = round(float((m.group(1) or m.group(2)).replace(",", ".")), 2)
        if value not in allowed:
            flags.append(f"price €{value:g} in the reply is not on any card or draft")
    if question.get("manual_check"):
        flags.append("manual check: " + question["manual_check"])
    return not failures, failures, flags


# ---------- running --------------------------------------------------------------------------------
def run_one(question, client, model):
    import guard
    import usage_log
    import agent
    from agent import chat
    from unittest.mock import patch
    from memory import Memory
    from prompts import STAFF_EMAIL
    started, before = time.perf_counter(), len(usage_log.entries)
    memory = Memory()
    canned = guard.screen_input(question["question"])
    outcome = {"blocked": bool(canned), "tools": []}
    tool_calls = []
    real_dispatch = agent.dispatch

    def recording_dispatch(name, arguments, mem):  # what the model asked for, so failures can be diagnosed
        result = real_dispatch(name, arguments, mem)
        info = result if isinstance(result, dict) else {}
        tool_calls.append({"tool": name, "arguments": str(arguments)[:400], "status": info.get("status"),
                           "wines": len(info.get("wines") or []), "error": str(info.get("error") or "")[:150] or None})
        return result
    try:
        if canned:
            outcome["reply"] = canned
        else:
            with patch.object(agent, "dispatch", recording_dispatch):
                outcome["reply"] = chat(client, model, memory, question["question"])
            outcome["problem"] = guard.reply_problem(outcome["reply"], (STAFF_EMAIL,))
    except Exception as error:  # a crashed run is a result, not a reason to stop the whole evaluation
        outcome["error"] = f"{type(error).__name__}: {str(error)[:100]}"
    outcome["tool_calls"] = tool_calls
    outcome["cards"] = (memory.recommendations or {}).get("wines", [])
    outcome["comparison"] = memory.comparison
    outcome["choices"] = memory.choices
    outcome["draft"] = memory.pending_order
    calls = usage_log.entries[before:]
    outcome["tools"] = [t for e in calls for t in e.get("tools", [])]
    failed_call = next((e for e in calls if e.get("error")), None)
    if failed_call and "error" not in outcome:  # chat() hides model errors in a polite reply: a failed call is never a pass
        outcome["error"] = f"model call failed: {failed_call['error']}"
    outcome["wall_s"] = round(time.perf_counter() - started, 2)
    outcome["calls"] = len([e for e in calls if not e.get("error")])
    outcome["prompt_tokens"] = sum(e.get("prompt_tokens", 0) for e in calls)
    outcome["completion_tokens"] = sum(e.get("completion_tokens", 0) for e in calls)
    costs = [e.get("cost") for e in calls if not e.get("error")]
    outcome["cost"] = sum(costs) if costs and all(isinstance(c, (int, float)) for c in costs) else None
    outcome["usage_missing"] = any("prompt_tokens" not in e for e in calls if not e.get("error"))
    return outcome


def run_all(questions, runs, label, out_path, pause):
    from llm_client import make_client
    client, model = make_client()
    rows = []
    with open(out_path, "w", encoding="utf-8") as handle:
        for q in questions:
            for run in range(1, runs + 1):
                outcome = run_one(q, client, model)
                passed, failures, flags = score(q, outcome)
                row = {"label": label or model, "model": model, "id": q["id"], "author": q["author"],
                       "category": q["category"], "behaviour": q["behaviour"], "run": run, "passed": passed,
                       "failures": failures, "flags": flags, "question": q["question"],
                       "reply": outcome.get("reply"), "wall_s": outcome["wall_s"], "calls": outcome["calls"],
                       "prompt_tokens": outcome["prompt_tokens"], "completion_tokens": outcome["completion_tokens"],
                       "cost": outcome["cost"], "usage_missing": outcome["usage_missing"],
                       "cards": [c.get("wine_id") for c in outcome.get("cards", [])],
                       "tool_calls": outcome.get("tool_calls", [])}
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                rows.append(row)
                print(f"[{'PASS' if passed else 'FAIL'}] {q['id']} run {run}: {'; '.join(failures)[:160]}")
                time.sleep(pause)
    return rows


def pct(values, share):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, round(share * (len(ordered) - 1))))] if ordered else None


def summarize(rows):
    out = []
    by_label = defaultdict(list)
    for r in rows:
        by_label[r["label"]].append(r)
    out.append("| Configuration | Runs | Pass rate | Stable questions | Median s | p95 s | Mean tokens (in/out) | Mean cost USD |")
    out.append("|---|---|---|---|---|---|---|---|")
    for label, rs in by_label.items():
        by_q = defaultdict(list)
        for r in rs:
            by_q[r["id"]].append(r["passed"])
        stable = sum(1 for v in by_q.values() if len(set(v)) == 1)
        wall = [r["wall_s"] for r in rs]
        costs = [r["cost"] for r in rs if r["cost"] is not None]
        out.append(f"| {label} | {len(rs)} | {100 * sum(r['passed'] for r in rs) / len(rs):.0f} % | {stable}/{len(by_q)} | "
                   f"{statistics.median(wall):.1f} | {pct(wall, .95):.1f} | "
                   f"{statistics.mean(r['prompt_tokens'] for r in rs):.0f} / {statistics.mean(r['completion_tokens'] for r in rs):.0f} | "
                   f"{('%.4f' % statistics.mean(costs)) if costs else 'n/a'} |")
    out.append("")
    out.append("| Configuration | Category | Runs | Pass rate |")
    out.append("|---|---|---|---|")
    for label, rs in by_label.items():
        cats = defaultdict(list)
        for r in rs:
            cats[r["category"]].append(r["passed"])
        for cat, v in sorted(cats.items()):
            out.append(f"| {label} | {cat} | {len(v)} | {100 * sum(v) / len(v):.0f} % |")
    failed = [r for rs in by_label.values() for r in rs if not r["passed"]]
    out.append("")
    out.append(f"{len(failed)} failed runs (details below; copy the real ones into FAILURES.md).")
    for r in failed[:40]:
        out.append(f"- [{r['label']}] {r['id']} run {r['run']}: {'; '.join(r['failures'])[:200]}")
    flagged = [r for r in rows if r["flags"]]
    out.append(f"\n{len(flagged)} runs have flags for a human to read (prices in text, manual checks, attacks that reached the model):")
    for r in flagged[:40]:
        out.append(f"- {r['id']} run {r['run']}: {'; '.join(r['flags'])[:200]}")
    if any(r.get("usage_missing") for r in rows):
        out.append("\nWarning: some calls had no token usage from the provider; token and cost columns are incomplete there.")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--questions", nargs="+", default=[str(next(p for p in (HERE / "eval_questions.csv", HERE / "eval_questions.json") if p.exists()))],
                        help="question files (.csv or .json); default: eval_questions.csv (or the old eval_questions.json)")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--label", default=None, help="name of this configuration, e.g. the model")
    parser.add_argument("--out", default=None)
    parser.add_argument("--pause", type=float, default=1.0, help="seconds between runs")
    parser.add_argument("--only", default=None, help="run only these question ids, comma separated, e.g. seed-csv06,seed-csv16")
    parser.add_argument("--check", action="store_true", help="validate questions only, no model calls")
    parser.add_argument("--summarize", nargs="+", metavar="RESULTS", help="summarise result files, no model calls")
    args = parser.parse_args(argv)
    if args.summarize:
        rows = [json.loads(line) for f in args.summarize for line in Path(f).read_text(encoding="utf-8").splitlines() if line.strip()]
        print(summarize(rows))
        return 0
    try:
        questions = load_questions(args.questions)
    except (ValueError, KeyError, OSError) as error:
        print(f"Could not read the questions file: {error}. Check that numbers are plain numbers and the file is saved as CSV UTF-8.")
        return 1
    if args.only:
        wanted = {part.strip() for part in args.only.split(",") if part.strip()}
        missing = wanted - {q["id"] for q in questions}
        if missing:
            print("Unknown question id(s): " + ", ".join(sorted(missing)))
            return 1
        questions = [q for q in questions if q["id"] in wanted]
    if not questions:
        print("No questions found in " + ", ".join(args.questions) + ". The file probably has only the header row: "
              "use the eval_questions.csv from the latest upload (it contains 16 seed questions).")
        return 1
    problems = validate_questions(questions)
    if problems:
        print("Fix these questions first:\n- " + "\n- ".join(problems))
        return 1
    print(f"{len(questions)} questions valid against the catalogue.")
    if args.check:
        return 0
    os.environ.setdefault("WINE_DATA_DIR", tempfile.mkdtemp(prefix="cave_eval_"))
    out = args.out or f"eval_results_{int(time.time())}.jsonl"
    os.environ.setdefault("USAGE_LOG_FILE", str(Path(out).with_suffix(".usage.jsonl")))
    import database
    database.initialize()
    rows = run_all(questions, args.runs, args.label, out, args.pause)
    print("\n" + summarize(rows) + f"\n\nSaved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
