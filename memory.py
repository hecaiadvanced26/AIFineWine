"""Keep complete recent turns and one application-owned order draft."""
import secrets


class Memory:
    def __init__(self, keep_turns=6):
        self.keep_turns = keep_turns
        self.messages = []
        self.pending_order = None
        self.conversation_id = secrets.token_hex(4)  # groups usage log lines; carries no personal data
        self.turn_number = 0
        self.reset_cards()

    def reset_cards(self):
        """Per-turn UI payloads set by tools: cards, comparison, quick replies."""
        self.recommendations = None
        self.comparison = None
        self.choices = None

    def start_turn(self, text):
        self.turn_number += 1
        self.messages.append({"role": "user", "content": text})
        starts = [i for i, message in enumerate(self.messages)
                  if message["role"] == "user"]
        if len(starts) > self.keep_turns:
            self.messages = self.messages[starts[-self.keep_turns]:]

    def add_reply(self, text):
        self.messages.append({"role": "assistant", "content": text})
