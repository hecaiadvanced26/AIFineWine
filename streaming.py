"""Print text fragments and collect complete tool calls from a stream."""


def collect_response(stream, on_text=None, on_status=None):
    text = ""
    calls = {}
    finish_reason = None
    for chunk in stream:
        if not chunk.choices:
            continue
        choice = chunk.choices[0]
        delta = choice.delta
        if choice.finish_reason:
            finish_reason = choice.finish_reason
        if delta.content:
            if not text and on_status:
                on_status("Writing reply…")
            text += delta.content
            if on_text:
                on_text(delta.content)
        for part in delta.tool_calls or []:
            if not calls and on_status:
                on_status("Model is preparing a tool request…")
            if part.index not in calls:
                calls[part.index] = {"id": "", "type": "function",
                                     "function": {"name": "", "arguments": ""}}
            call = calls[part.index]
            if part.id:
                call["id"] = part.id
            if part.function:
                call["function"]["name"] += part.function.name or ""
                call["function"]["arguments"] += part.function.arguments or ""
    if finish_reason not in ("stop", "tool_calls"):
        raise ValueError("Model stream did not finish normally.")
    message = {"role": "assistant", "content": text or None}
    if calls:
        message["tool_calls"] = [calls[index] for index in sorted(calls)]
        for call in message["tool_calls"]:
            if not call["id"] or not call["function"]["name"]:
                raise ValueError("Incomplete streamed tool call.")
    return message
