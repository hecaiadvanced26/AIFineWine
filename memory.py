"""Keep complete recent turns and one application-owned order draft."""


class Memory:
    def __init__(self, keep_turns=6):
        self.keep_turns = keep_turns
        self.messages = []
        self.pending_order = None

    def start_turn(self, text):
        self.messages.append({"role": "user", "content": text})
        starts = [i for i, message in enumerate(self.messages)
                  if message["role"] == "user"]
        if len(starts) > self.keep_turns:
            self.messages = self.messages[starts[-self.keep_turns]:]

    def add_reply(self, text):
        self.messages.append({"role": "assistant", "content": text})
