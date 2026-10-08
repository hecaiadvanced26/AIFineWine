"""Run the introductory terminal demo."""
import json
import os
import sqlite3

from openai import OpenAI

from agent import chat
from database import initialize
from memory import Memory
from orders import submit_order


def display_chunk(text):
    print(text, end="", flush=True)


def main():
    key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not key or not model:
        print("Set OPENAI_API_KEY and OPENAI_MODEL first. See README.md.")
        return
    client = OpenAI(api_key=key, base_url=os.getenv("OPENAI_BASE_URL") or None,
                    timeout=30, max_retries=1)
    initialize()
    memory = Memory()
    print("Wine assistant — fictional catalog, local demo orders.")
    print("Commands: /confirm, /cancel, /quit")
    while True:
        try:
            text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if text == "/quit":
            break
        if not text:
            continue
        if text == "/cancel":
            memory.pending_order = None
            print("Order draft cancelled.")
            memory.start_turn(text)
            memory.add_reply("Order draft cancelled.")
            continue
        if text == "/confirm":
            if memory.pending_order is None:
                print("No draft to confirm. Choose a wine and quantity first.")
                continue
            try:
                result = submit_order(memory.pending_order)
            except (OSError, sqlite3.Error):
                print("Export failed. Retry /confirm; the same order ID prevents duplicates.")
                continue
            memory.pending_order = None
            print(json.dumps(result, indent=2))
            memory.start_turn(text)
            memory.add_reply(json.dumps(result))
            continue
        print("\nAssistant: ", end="", flush=True)
        chat(client, model, memory, text, on_text=display_chunk)
        print()
        if memory.pending_order:
            print("\nExact order draft:")
            print(json.dumps(memory.pending_order, indent=2))
            print("Type /confirm to export it, or /cancel. Other messages discard this draft.")


if __name__ == "__main__":
    main()
