"""Check status timing against actual streamed model and tool operations."""
import unittest
from contextlib import nullcontext
from types import SimpleNamespace as NS
from unittest.mock import patch

from agent import chat
from memory import Memory


def chunk(text=None, calls=None, finish=None):
    return NS(choices=[NS(delta=NS(content=text, tool_calls=calls), finish_reason=finish)])


class StatusTests(unittest.TestCase):
    def test_query_status_before_dispatch_and_text_status_before_text(self):
        events = []
        tool = NS(index=0, id="lookup", function=NS(
            name="run_query", arguments='{"sql":"SELECT name FROM wines"}'))
        streams = iter([[chunk(calls=[tool]), chunk(finish="tool_calls")],
                        [chunk(text="Wine A"), chunk(finish="stop")]])

        def create(**kwargs):
            self.assertEqual(events[-1], "Contacting model…")
            return nullcontext(iter(next(streams)))

        def dispatch(*args):
            self.assertEqual(events[-1], "Looking up catalog data…")
            return {"status": "ok", "rows": [{"name": "Wine A"}]}

        def on_text(text):
            self.assertEqual(events[-1], "Writing reply…")

        client = NS(chat=NS(completions=NS(create=create)))
        with patch("agent.dispatch", side_effect=dispatch):
            self.assertEqual(chat(client, "fake", Memory(), "search", on_text,
                                  events.append), "Wine A")
        self.assertEqual(events, ["Contacting model…", "Model is preparing a tool request…",
                                  "Looking up catalog data…", "Contacting model…",
                                  "Writing reply…", "Reply complete."])

    def test_failed_stream_reports_failure_not_completion(self):
        events = []
        client = NS(chat=NS(completions=NS(create=lambda **kw: nullcontext(
            iter([chunk(text="Partial"), chunk(finish="length")])))))
        memory = Memory()
        reply = chat(client, "fake", memory, "hello", on_status=events.append)
        self.assertIn("interrupted", reply)
        self.assertEqual(events[-1], "Reply failed — please retry.")
        self.assertNotIn("Looking up catalog data…", events)
        self.assertNotIn("Reply complete.", events)
        self.assertIsNone(memory.pending_order)


if __name__ == "__main__":
    unittest.main()
