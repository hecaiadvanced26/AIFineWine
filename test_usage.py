"""Usage logging and cost report: arithmetic checked against hand-computed numbers (synthetic data, not measurements)."""
import os as _os
_os.environ.setdefault("USAGE_LOG", "0")  # tests must not write data/usage_log.jsonl
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch

import agent
import cost_report
import usage_log
from memory import Memory
from streaming import collect_response, read_usage


def chunk(content=None, finish=None, usage=None, tool=None):
    delta = NS(content=content, tool_calls=tool)
    return NS(choices=[NS(delta=delta, finish_reason=finish)] if (content is not None or finish or tool) else [],
              usage=usage)


class StreamUsageTests(unittest.TestCase):
    def test_usage_in_last_chunk_without_choices_is_captured(self):
        usage = NS(prompt_tokens=1200, completion_tokens=80, total_tokens=1280, cost=0.0031,
                   prompt_tokens_details=NS(cached_tokens=1000), completion_tokens_details=NS(reasoning_tokens=20))
        stats = {}
        message = collect_response(iter([chunk("Hel"), chunk("lo", finish="stop"), chunk(usage=usage)]), stats=stats)
        self.assertEqual(message["content"], "Hello")
        self.assertEqual({k: stats[k] for k in ("prompt_tokens", "completion_tokens", "cost", "cached_tokens",
                                                "reasoning_tokens")},
                         {"prompt_tokens": 1200, "completion_tokens": 80, "cost": 0.0031, "cached_tokens": 1000,
                          "reasoning_tokens": 20})
        self.assertEqual(stats["finish_reason"], "stop")
        self.assertIn("first_token_s", stats)

    def test_dict_usage_and_missing_usage(self):
        self.assertEqual(read_usage({"prompt_tokens": 5, "completion_tokens": 2, "cost": None}),
                         {"prompt_tokens": 5, "completion_tokens": 2})
        self.assertEqual(read_usage(None), {})
        stats = {}
        collect_response(iter([chunk("ok", finish="stop")]), stats=stats)
        self.assertNotIn("prompt_tokens", stats)  # provider sent none: stays unknown, never guessed

    def test_old_call_style_still_works(self):
        self.assertEqual(collect_response(iter([chunk("x", finish="stop")]))["content"], "x")


class AgentLoggingTests(unittest.TestCase):
    def setUp(self):
        usage_log.entries.clear()

    def run_chat(self, side_effect):
        client = MagicMock()
        client.chat.completions.create.return_value.__enter__.return_value = object()
        memory = Memory()
        with patch.object(agent, "collect_response", side_effect=side_effect):
            agent.chat(client, "fake-model", memory, "my secret question text")
        return memory, client

    def test_each_call_is_logged_without_message_text(self):
        def fake(stream, on_text=None, on_status=None, stats=None):
            stats.update({"prompt_tokens": 900, "completion_tokens": 40, "cost": 0.001})
            return {"role": "assistant", "content": "Here you go."}
        memory, client = self.run_chat(fake)
        self.assertEqual(len(usage_log.entries), 1)
        entry = usage_log.entries[0]
        self.assertEqual((entry["conversation"], entry["turn"], entry["step"], entry["model"]),
                         (memory.conversation_id, 1, 1, "fake-model"))
        self.assertEqual(entry["prompt_tokens"], 900)
        self.assertNotIn("secret", json.dumps(entry))
        kwargs = client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["stream_options"], {"include_usage": True})
        self.assertEqual(kwargs["max_tokens"], agent.MAX_OUTPUT_TOKENS)
        self.assertGreaterEqual(agent.MAX_OUTPUT_TOKENS, 2000)  # reasoning models need room

    def test_failed_call_is_logged_as_error(self):
        def fake(*args, **kwargs):
            raise ValueError("Model stream did not finish normally.")
        self.run_chat(fake)
        self.assertEqual(usage_log.entries[0]["error"], "ValueError")

    def test_turn_numbers_increase_per_conversation(self):
        memory = Memory()
        memory.start_turn("a")
        memory.start_turn("b")
        self.assertEqual(memory.turn_number, 2)
        self.assertNotEqual(Memory().conversation_id, memory.conversation_id)


def row(conv, turn, step, p, c, cost=None, lat=1.0, **extra):
    base = {"conversation": conv, "turn": turn, "step": step, "model": "m", "prompt_tokens": p,
            "completion_tokens": c, "latency_s": lat}
    if cost is not None:
        base["cost"] = cost
    return {**base, **extra}


class CostReportTests(unittest.TestCase):
    def test_computed_cost_projection_matches_hand_calculation(self):
        # conversation A: 2 calls in turn 1 (1000+100, 2000+300). Prices: 0.5 USD in, 2 USD out per 1M tokens.
        rows = [row("A", 1, 1, 1000, 100), row("A", 1, 2, 2000, 300), row("B", 1, 1, 1000, 100)]
        # A cost = (3000*0.5 + 400*2)/1e6 = 0.0023 ; B cost = (1000*0.5 + 100*2)/1e6 = 0.0007 ; mean = 0.0015
        text = cost_report.report(rows, price_in=0.5, price_out=2.0)
        self.assertIn("mean USD 0.0015 over 2 conversations", text)
        self.assertIn("| 1,000 | 1.50 | 0.0015 |", text)
        self.assertIn("computed from the prices you passed", text)

    def test_reported_cost_wins_and_missing_prices_are_not_invented(self):
        rows = [row("A", 1, 1, 1000, 100, cost=0.01), row("B", 1, 1, 500, 50, cost=0.03)]
        self.assertIn("mean USD 0.0200", cost_report.report(rows))
        self.assertIn("provider-reported", cost_report.report(rows))
        without = cost_report.report([row("A", 1, 1, 1000, 100)])
        self.assertIn("No cost available", without)
        self.assertNotIn("| 1,000 |", without)

    def test_percentiles_and_errors(self):
        rows = [row("A", t, 1, 100, 10, cost=0.001, lat=float(t)) for t in range(1, 21)]
        rows.append({"conversation": "A", "turn": 99, "step": 1, "error": "ValueError", "latency_s": 9})
        text = cost_report.report(rows)
        self.assertIn("(1 failed)", text)
        self.assertIn("| Latency per turn, seconds (sum of model calls) | 10.5 | 10.5 | 19.0 |", text)

    def test_vercel_log_lines_are_parsed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "export.txt"
            path.write_text('2026-10-09 10:00 INFO noise\n2026-10-09 10:00 USAGE ' + json.dumps(
                row("A", 1, 1, 10, 5, cost=0.1)) + "\nUSAGE not json\n", encoding="utf-8")
            self.assertEqual(len(cost_report.load([path], vercel=True)), 1)


if __name__ == "__main__":
    unittest.main()
