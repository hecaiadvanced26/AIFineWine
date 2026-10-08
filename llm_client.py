"""One place that builds the model client for the evaluation runner (the app files still build their own)."""
import os

from openai import OpenAI


def settings():
    key, model = os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_MODEL")
    if not key or not model:
        raise SystemExit("Set OPENAI_API_KEY and OPENAI_MODEL first (see HOW_TO_RUN.md).")
    return key, model, os.getenv("OPENAI_BASE_URL") or None


def make_client():
    key, model, base_url = settings()
    return OpenAI(api_key=key, base_url=base_url, timeout=60, max_retries=1), model
