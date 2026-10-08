"""A small model → tools → model loop."""
import json

from httpx import HTTPError
from openai import APIError

from prompts import SYSTEM_PROMPT
from streaming import collect_response
from tools import TOOLS, dispatch

MAX_STEPS = 4
MAX_TOOL_CALLS = 6


def chat(client, model, memory, text, on_text=None, on_status=None):
    # A changed request requires a new draft and confirmation.
    memory.pending_order = None
    memory.start_turn(text)
    calls_used = 0
    invalid_calls = 0
    for step in range(MAX_STEPS):
        try:
            if on_status:
                on_status("Contacting model…")
            with client.chat.completions.create(
                model=model, messages=[{"role": "system", "content": SYSTEM_PROMPT}]
                + memory.messages, tools=TOOLS, stream=True,
                tool_choice="none" if step == MAX_STEPS - 1 else "auto") as stream:
                message = collect_response(stream, on_text, on_status)
        except (APIError, HTTPError, ValueError):
            memory.pending_order = None
            reply = "Model reply failed or was interrupted. Please try again."
            memory.add_reply(reply)
            if on_text:
                on_text("\n" + reply)
            if on_status:
                on_status("Reply failed — please retry.")
            return reply
        if not message.get("tool_calls"):
            reply = message["content"] or "I could not produce an answer. Please clarify."
            memory.add_reply(reply)
            if not message["content"] and on_text:
                on_text(reply)
            if on_status:
                on_status("Reply complete.")
            return reply
        memory.messages.append(message)
        if message["content"] and on_text:
            on_text("\n")
        for call in message["tool_calls"]:
            calls_used += 1
            if calls_used > MAX_TOOL_CALLS or invalid_calls >= 2:
                result = {"error": "Tool budget reached. Ask the customer to clarify."}
            else:
                if on_status:
                    on_status({"run_query": "Looking up catalog data…",
                               "prepare_order": "Checking stock and preparing order…"}
                              .get(call["function"]["name"], "Checking tool request…"))
                result = dispatch(call["function"]["name"], call["function"]["arguments"], memory)
                if on_status and (result.get("error") or result.get("status") in
                                  ("invalid_arguments", "query_error")):
                    on_status("Tool returned a problem; sending it back to model…")
                if result.get("status") in ("invalid_arguments", "query_error"):
                    invalid_calls += 1
            memory.messages.append({"role": "tool", "tool_call_id": call["id"],
                                    "content": json.dumps(result)})
    memory.pending_order = None
    reply = "I could not complete this request within the tool budget. Please clarify."
    memory.add_reply(reply)
    if on_text:
        on_text(reply)
    if on_status:
        on_status("Step limit reached — please clarify.")
    return reply
