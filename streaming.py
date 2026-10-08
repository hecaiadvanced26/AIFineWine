"""Print text fragments and collect complete tool calls from a stream."""
import time


def _number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def read_usage(usage):
    """Pick the token counts out of a provider usage object (OpenRouter puts it in the last chunk)."""
    if usage is None:
        return {}
    get = (lambda key: usage.get(key)) if isinstance(usage, dict) else (lambda key: getattr(usage, key, None))
    def inner(parent, key):
        detail = get(parent)
        if detail is None:
            return None
        return detail.get(key) if isinstance(detail, dict) else getattr(detail, key, None)
    found = {"prompt_tokens": get("prompt_tokens"), "completion_tokens": get("completion_tokens"),
             "total_tokens": get("total_tokens"), "cost": get("cost"),
             "cached_tokens": inner("prompt_tokens_details", "cached_tokens"),
             "reasoning_tokens": inner("completion_tokens_details", "reasoning_tokens")}
    return {key: _number(value) for key, value in found.items() if _number(value) is not None}


def collect_response(stream, on_text=None, on_status=None, stats=None):
    """Return the assistant message. If `stats` (a dict) is given, fill it with usage and timing."""
    text = ""
    calls = {}
    finish_reason = None
    started = time.perf_counter()
    for chunk in stream:
        if stats is not None and getattr(chunk, "usage", None):
            stats.update(read_usage(chunk.usage))
        if not chunk.choices:
            continue
        choice = chunk.choices[0]
        delta = choice.delta
        if choice.finish_reason:
            finish_reason = choice.finish_reason
        if stats is not None and "first_token_s" not in stats and (delta.content or delta.tool_calls):
            stats["first_token_s"] = round(time.perf_counter() - started, 3)
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
    if stats is not None:
        stats["finish_reason"] = finish_reason
    if finish_reason not in ("stop", "tool_calls"):
        raise ValueError("Model stream did not finish normally.")
    message = {"role": "assistant", "content": text or None}
    if calls:
        message["tool_calls"] = [calls[index] for index in sorted(calls)]
        for call in message["tool_calls"]:
            if not call["id"] or not call["function"]["name"]:
                raise ValueError("Incomplete streamed tool call.")
    return message
