"""Record token usage, cost and latency per model call. Never stores message text.

Each model call writes one JSON line: to stdout with the prefix "USAGE " (Vercel keeps stdout in its logs) and, when a
writable data folder exists, to data/usage_log.jsonl. `cost_report.py` reads either. In-process `entries` lets tests
and `eval_run.py` sum usage per question without files.
"""
import json
import os
import sys
import threading
import time
from pathlib import Path

entries = []  # this process only
_lock = threading.Lock()
MAX_ENTRIES = 5000


def log_path():
    folder = os.environ.get("WINE_DATA_DIR") or str(Path(__file__).parent / "data")
    return Path(os.environ.get("USAGE_LOG_FILE") or Path(folder) / "usage_log.jsonl")


def record(conversation, turn, step, model, stats, latency_s, tools=(), error=None):
    entry = {"ts": round(time.time(), 3), "conversation": conversation, "turn": turn, "step": step,
             "model": model, "latency_s": round(latency_s, 3), "tools": list(tools)}
    entry.update({k: v for k, v in (stats or {}).items()})
    if error:
        entry["error"] = str(error)[:80]
    with _lock:
        entries.append(entry)
        del entries[:-MAX_ENTRIES]
    line = json.dumps(entry, ensure_ascii=False)
    print("USAGE " + line, file=sys.stderr if os.environ.get("USAGE_TO_STDERR") else sys.stdout, flush=True)
    if os.environ.get("USAGE_LOG", "1") != "0":
        try:
            path = log_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except OSError:
            pass  # read-only or missing folder (e.g. some serverless runtimes): stdout still has it
    return entry
