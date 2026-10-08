"""Offline browser checks; no model calls, catalog changes or order exports."""
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


def fake_chat(client, model, memory, text, on_text=None, on_status=None):
    memory.pending_order = None
    memory.start_turn(text)
    for event in ("Contacting model…", "Looking up catalog data…", "Writing reply…"):
        on_status(event)
    on_text("Wine A ")
    on_text("costs €12.")
    if text == "prepare":
        memory.pending_order = {"order_id": "test-order", "wine_id": "DEMO-001",
                                "name": "Wine A", "vintage": 2023,
                                "quantity": 2, "total_cents": 2400}
    reply = "Wine A costs €12."
    memory.add_reply(reply)
    on_status("Reply complete.")
    return reply


class BrowserTests(unittest.TestCase):
    def setUp(self):
        for mock in (patch.dict(os.environ, OPENAI_API_KEY="test-only", OPENAI_MODEL="fake"),
                     patch("database.initialize"), patch("agent.chat", side_effect=fake_chat)):
            mock.start()
            self.addCleanup(mock.stop)
        self.submit = patch("orders.submit_order").start()
        self.addCleanup(patch.stopall)
        self.app = AppTest.from_file(str(Path(__file__).with_name("ui.py"))).run()

    def button(self, label):
        return next(button for button in self.app.button if button.label == label)

    def test_chat_and_status(self):
        self.assertFalse(self.app.exception)
        self.app.chat_input[0].set_value("search").run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.chat_message[-1].markdown[-1].value, "Wine A costs €12.")
        self.assertEqual(self.app.status[0].label, "Reply complete.")
        self.assertEqual(self.app.status[0].state, "complete")
        self.assertIn("Looking up catalog data…", [m.value for m in self.app.status[0].markdown])
        self.submit.assert_not_called()

    def test_explicit_confirmation(self):
        self.app.chat_input[0].set_value("prepare").run()
        self.submit.assert_not_called()
        self.submit.return_value = {"order_id": "test-order", "status": "exported_locally"}
        self.button("Confirm order").click().run()
        self.assertFalse(self.app.exception)
        self.submit.assert_called_once()
        self.assertIsNone(self.app.session_state.memory.pending_order)
        self.app.run()
        self.submit.assert_called_once()

    def test_failed_export_keeps_draft(self):
        self.app.chat_input[0].set_value("prepare").run()
        self.submit.side_effect = OSError("test export failure")
        self.button("Confirm order").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.session_state.memory.pending_order["order_id"], "test-order")
        self.assertTrue(self.app.error)

    def test_cancel_and_new_conversation(self):
        self.app.chat_input[0].set_value("prepare").run()
        self.button("Cancel order").click().run()
        self.assertIsNone(self.app.session_state.memory.pending_order)
        self.submit.assert_not_called()
        self.button("New conversation").click().run()
        self.assertEqual(self.app.session_state.history, [])
        self.assertEqual(self.app.session_state.memory.messages, [])

    def test_changed_request_discards_draft(self):
        self.app.chat_input[0].set_value("prepare").run()
        self.app.chat_input[0].set_value("search").run()
        self.assertIsNone(self.app.session_state.memory.pending_order)
        self.assertNotIn("Confirm order", [b.label for b in self.app.button])


if __name__ == "__main__":
    unittest.main()
