"""Summarise usage_log.jsonl: tokens, latency and cost per turn and per conversation, plus a monthly projection.

    python cost_report.py                                   # reads data/usage_log.jsonl
    python cost_report.py usage.jsonl more.jsonl            # one or more files
    python cost_report.py --from-vercel-logs export.txt     # lines containing "USAGE {...}" (Vercel log export)
    python cost_report.py --price-in 0.25 --price-out 2.00  # USD per 1M tokens, copy them from the model's OpenRouter page

Cost: if the provider reported `cost` (OpenRouter does), that real number is used. Otherwise it is computed from the
prices you pass. Prices are NOT built in, because they change; the projection is only as good as the prices and the
conversation mix you measured. Message text is never in the log.
"""
import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def load(paths, vercel=False):
    rows = []
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
            if vercel:
                if "USAGE {" not in line:
                    continue
                line = line[line.index("USAGE {") + 6:]
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def percentile(values, share):
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(share * (len(ordered) - 1))))
    return ordered[index]


def call_cost(row, price_in, price_out):
    if isinstance(row.get("cost"), (int, float)):
        return row["cost"], "reported"
    if price_in is not None and price_out is not None and "prompt_tokens" in row and "completion_tokens" in row:
        return (row["prompt_tokens"] * price_in + row["completion_tokens"] * price_out) / 1_000_000, "computed"
    return None, "unknown"


def summarise(rows, price_in=None, price_out=None):
    ok = [r for r in rows if not r.get("error")]
    turns = defaultdict(list)
    conversations = defaultdict(set)
    for row in ok:
        key = (row.get("conversation"), row.get("turn"))
        turns[key].append(row)
        conversations[row.get("conversation")].add(row.get("turn"))
    turn_stats = []
    for key, calls in turns.items():
        costs = [call_cost(c, price_in, price_out) for c in calls]
        known = [c for c, _ in costs if c is not None]
        turn_stats.append({
            "key": key, "calls": len(calls),
            "prompt": sum(c.get("prompt_tokens", 0) for c in calls),
            "completion": sum(c.get("completion_tokens", 0) for c in calls),
            "latency": sum(c.get("latency_s", 0) for c in calls),
            "cost": sum(known) if len(known) == len(calls) else None,
            "kinds": {k for _, k in costs}})
    per_conv = defaultdict(lambda: {"turns": 0, "cost": 0.0, "complete": True, "tokens": 0})
    for t in turn_stats:
        c = per_conv[t["key"][0]]
        c["turns"] += 1
        c["tokens"] += t["prompt"] + t["completion"]
        if t["cost"] is None:
            c["complete"] = False
        else:
            c["cost"] += t["cost"]
    return {"calls": len(rows), "errors": len(rows) - len(ok), "turns": turn_stats, "conversations": dict(per_conv),
            "ok_calls": ok}


def fmt(value, digits=2):
    return "n/a" if value is None else f"{value:.{digits}f}"


def report(rows, price_in=None, price_out=None, scenarios=(100, 1000, 10000)):
    data = summarise(rows, price_in, price_out)
    out = []
    turns, convs = data["turns"], data["conversations"]
    if not turns:
        return "No successful model calls in the log."
    lat = [t["latency"] for t in turns]
    call_lat = [c.get("latency_s") for c in data["ok_calls"] if c.get("latency_s") is not None]
    ttft = [c["first_token_s"] for c in data["ok_calls"] if "first_token_s" in c]
    out.append(f"Model calls: {data['calls']} ({data['errors']} failed). Turns: {len(turns)}. Conversations: {len(convs)}.")
    out.append("")
    out.append("| Measure | Mean | Median | 95th percentile |")
    out.append("|---|---|---|---|")
    def row(name, values, digits=0):
        out.append(f"| {name} | {fmt(statistics.mean(values), digits)} | {fmt(statistics.median(values), digits)} | "
                   f"{fmt(percentile(values, .95), digits)} |")
    row("Model calls per turn", [t["calls"] for t in turns], 1)
    row("Prompt tokens per turn", [t["prompt"] for t in turns])
    row("Completion tokens per turn", [t["completion"] for t in turns])
    row("Latency per turn, seconds (sum of model calls)", lat, 1)
    row("Latency per model call, seconds", call_lat, 1)
    if ttft:
        row("Time to first token, seconds", ttft, 2)
    known_turns = [t["cost"] for t in turns if t["cost"] is not None]
    if known_turns:
        row("Cost per turn, USD", known_turns, 5)
    out.append("")
    cached = [c.get("cached_tokens") for c in data["ok_calls"] if c.get("cached_tokens") is not None]
    prompt_total = sum(t["prompt"] for t in turns)
    if cached and prompt_total:
        out.append(f"Cached prompt tokens: {sum(cached)} of {prompt_total} ({100 * sum(cached) / prompt_total:.0f} %).")
    reasoning = [c.get("reasoning_tokens") for c in data["ok_calls"] if c.get("reasoning_tokens")]
    if reasoning:
        out.append(f"Reasoning tokens (billed as output): {sum(reasoning)}.")
    completion_total = sum(t["completion"] for t in turns)
    if prompt_total + completion_total:
        out.append(f"Input share of all tokens: {100 * prompt_total / (prompt_total + completion_total):.0f} %.")
    complete = [c for c in convs.values() if c["complete"]]
    out.append("")
    if complete:
        mean_cost = statistics.mean(c["cost"] for c in complete)
        mean_turns = statistics.mean(c["turns"] for c in complete)
        kinds = set().union(*[t["kinds"] for t in turns])
        source = "provider-reported" if kinds == {"reported"} else "computed from the prices you passed" \
            if kinds == {"computed"} else "mixed reported and computed"
        out.append(f"Cost per conversation: mean USD {mean_cost:.4f} over {len(complete)} conversations "
                   f"(mean {mean_turns:.1f} turns each; {source}).")
        out.append("")
        out.append("Projection = conversations per month x mean cost per conversation. It assumes your measured "
                   "conversations are typical, which you should state on the slide.")
        out.append("")
        out.append("| Conversations per month | Estimated cost, USD per month | Per conversation, USD |")
        out.append("|---|---|---|")
        for n in scenarios:
            out.append(f"| {n:,} | {n * mean_cost:,.2f} | {mean_cost:.4f} |")
    else:
        out.append("No cost available: the provider reported none and no prices were given. "
                   "Pass --price-in and --price-out (USD per 1M tokens, from the model's OpenRouter page).")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", default=[str(Path(__file__).parent / "data" / "usage_log.jsonl")])
    parser.add_argument("--from-vercel-logs", action="store_true", help="files are Vercel log exports")
    parser.add_argument("--price-in", type=float, help="USD per 1M prompt tokens")
    parser.add_argument("--price-out", type=float, help="USD per 1M completion tokens")
    args = parser.parse_args(argv)
    missing = [f for f in args.files if not Path(f).exists()]
    if missing:
        print("File not found: " + ", ".join(missing) + "\nUse the app or eval_run.py first so a log exists.")
        return 1
    print(report(load(args.files, args.from_vercel_logs), args.price_in, args.price_out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
