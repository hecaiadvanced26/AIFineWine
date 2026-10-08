"""Local React demo server. JSON-lines carry real agent events to the browser."""
import json
import os
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from pathlib import Path
from queue import Queue
from threading import Lock, Thread

from flask import Flask, Response, jsonify, redirect, request, session, send_from_directory
from openai import OpenAI

import guard
from agent import chat
from database import initialize
from catalog import get_wine_details
from make_wine_images import bottle_svg
from memory import Memory
from orders import prepare_order, submit_order
from prompts import STAFF_EMAIL

FRONTEND = Path(__file__).parent / "frontend" / "dist"
app = Flask(__name__, static_folder=str(FRONTEND / "assets"), static_url_path="/assets")
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(MAX_CONTENT_LENGTH=16_384, SESSION_COOKIE_SAMESITE="Strict",
                  SESSION_COOKIE_SECURE=bool(os.getenv("VERCEL")))
conversations = {}  # Local demo only: memory is cleared when the server restarts.

if os.getenv("VERCEL"):
    initialize()


RATE_LIMIT, RATE_WINDOW, SESSION_TURN_LIMIT = 15, 60, 80
hits = defaultdict(deque)  # per client; in-memory, so per server instance only (Vercel: per cold instance)


def rate_limited():
    """Sliding window per client address; the platform sets X-Forwarded-For on Vercel."""
    client = (request.headers.get("X-Forwarded-For", "") or request.remote_addr or "?").split(",")[0].strip()
    now = time.monotonic()
    window = hits[client]
    while window and now - window[0] > RATE_WINDOW:
        window.popleft()
    if len(window) >= RATE_LIMIT:
        return True
    window.append(now)
    if len(hits) > 5000:  # keep the table small
        for key in [k for k, v in hits.items() if not v or now - v[-1] > RATE_WINDOW][:2500]:
            hits.pop(key, None)
    return False


@app.get("/api/health")
def health_route():
    return jsonify(ok=True, storage="temporary" if os.getenv("VERCEL") else "local")


def conversation():
    if "chat_id" not in session:
        session["chat_id"] = secrets.token_hex(16)
    return conversations.setdefault(session["chat_id"], {"memory": Memory(), "lock": Lock()})


@app.before_request
def same_origin():
    if request.method == "POST" and request.headers.get("Origin") not in (
            None, request.host_url.rstrip("/")):
        return jsonify(error="Cross-origin requests are not allowed."), 403


@app.get("/favicon.svg")
def favicon_route():
    """Tab icon. On Vercel the file is normally served from public/; this route covers local runs and any gap."""
    return send_from_directory(FRONTEND, "favicon.svg", mimetype="image/svg+xml", max_age=3600)


@app.get("/favicon.ico")
def favicon_ico_route():
    """Browsers ask for /favicon.ico by habit; point them at the SVG."""
    return redirect("/favicon.svg", code=302)


@app.get("/cave_wine_list.pdf")
def wine_list_route():
    """Full wine list for customers. On Vercel the file is served from public/; this route covers local runs."""
    return send_from_directory(FRONTEND, "cave_wine_list.pdf", mimetype="application/pdf", max_age=300)


@app.get("/")
def index():
    conversation()  # Set the session cookie before the first streamed response.
    # Vercel fixes file mtimes; same-size HTML can reuse an ETag across builds.
    response = send_from_directory(FRONTEND, "index.html", conditional=False, etag=False)
    response.headers["Cache-Control"] = "no-store"
    response.headers.pop("Last-Modified", None)
    return response


@app.get("/api/wine-image/<wine_id>.svg")
def wine_image_route(wine_id):
    """Generated bottle illustration (not a product photo). Unknown IDs get a generic bottle."""
    wine = get_wine_details(wine_id)
    if "error" in wine:
        svg = bottle_svg("Wine", "", None, None)
    else:
        svg = bottle_svg(wine["name"], wine.get("winery"), wine["vintage"], wine.get("wine_type"))
    return Response(svg, mimetype="image/svg+xml", headers={
        "Cache-Control": "public, max-age=3600", "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'"})


@app.post("/api/chat")
def chat_route():
    data = request.get_json()
    text = data.get("text") if isinstance(data, dict) else None
    if not isinstance(text, str) or not text.strip() or len(text) > 4000:
        return jsonify(error="Enter a message of 1–4,000 characters."), 400
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL"):
        return jsonify(error="API settings missing. Check .env and restart."), 503
    if rate_limited():
        app.logger.warning("Rate limit hit")
        return jsonify(error="Too many messages. Please wait a minute."), 429
    state = conversation()
    state["turns"] = state.get("turns", 0) + 1
    if state["turns"] > SESSION_TURN_LIMIT:
        return jsonify(error="This conversation is long. Start a new conversation."), 429
    canned = guard.screen_input(text)
    if canned:  # the model never sees it and memory never stores it
        app.logger.warning("Input blocked by guard")
        lines = [{"type": "text", "text": canned}, {"type": "done", "reply": canned, "draft": state["memory"].pending_order,
                                                     "recommendations": None, "comparison": None, "choices": None}]
        return Response("".join(json.dumps(line) + "\n" for line in lines), mimetype="application/x-ndjson",
                        headers={"Cache-Control": "no-store"})
    if not state["lock"].acquire(blocking=False):
        return jsonify(error="Another request is running. Please wait."), 409
    events = Queue()
    shown = {"text": "", "stopped": False}

    def stream_text(value):
        """Stop streaming as soon as the text so far breaks a rule; the final reply is checked again."""
        shown["text"] += value
        if shown["stopped"] or guard.reply_problem(shown["text"], (STAFF_EMAIL,)):
            shown["stopped"] = True
            return
        emit("text", text=value)

    def emit(kind, **payload):
        events.put({"type": kind, **payload})

    def run():
        try:
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                            base_url=os.getenv("OPENAI_BASE_URL") or None,
                            timeout=30, max_retries=1)
            reply = chat(client, os.environ["OPENAI_MODEL"], state["memory"], text.strip(),
                         on_text=stream_text,
                         on_status=lambda value: emit("status", text=value))
            memory = state["memory"]
            emit("done", reply=reply, draft=memory.pending_order, recommendations=memory.recommendations,
                 comparison=memory.comparison, choices=memory.choices)
        except Exception:
            # Do not leak provider details or leave a draft after an unexpected failure.
            app.logger.exception("Chat request failed")
            state["memory"] = Memory()
            emit("error", text="Request failed. Conversation reset; please try again.")
        finally:
            state["lock"].release()
            events.put(None)

    Thread(target=run, daemon=True).start()

    def stream():
        while (event := events.get()) is not None:
            yield json.dumps(event) + "\n"

    return Response(stream(), mimetype="application/x-ndjson",
                    headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


@app.post("/api/order")
def order_route():
    data = request.get_json()
    if not isinstance(data, dict) or data.get("action") not in ("confirm", "cancel", "quantity"):
        return jsonify(error="Choose confirm, cancel or quantity."), 400
    state = conversation()
    with state["lock"]:
        memory = state["memory"]
        draft = memory.pending_order
        if not draft or data.get("order_id") != draft["order_id"]:
            return jsonify(error="Draft no longer current. Prepare a new order.", draft=None), 409
        if data["action"] == "quantity":
            quantity = data.get("quantity")
            updated = prepare_order(draft["wine_id"], quantity)  # Price and stock come from the database.
            if "error" in updated:
                return jsonify(error=updated["error"], draft=draft), 400
            memory.pending_order = updated
            memory.start_turn(f"Change the quantity to {quantity}")
            memory.add_reply(f"Draft updated: {quantity} x {updated['name']}. Awaiting confirmation.")
            return jsonify(reply=None, draft=updated, confirmation=None)
        if data["action"] == "cancel":
            reply = "Order draft cancelled. Nothing was submitted."
            confirmation = None
        else:
            try:
                result = submit_order(draft)  # Always use server-side draft, never client prices.
            except (OSError, sqlite3.Error):
                return jsonify(error="Export failed. Retry with the same order ID.", draft=draft), 503
            reply = result.get("error") or f"Order {result['order_id']} exported locally. No payment taken."
            confirmation = None if result.get("error") else {**draft, "order_id": result["order_id"]}
        memory.pending_order = None
        memory.start_turn(data["action"] + " order")
        memory.add_reply(reply)
        return jsonify(reply=reply, draft=None, confirmation=confirmation)


@app.post("/api/reset")
def reset_route():
    state = conversation()
    with state["lock"]:
        state["memory"] = Memory()
        state["turns"] = 0
    return jsonify(ok=True)


if __name__ == "__main__":
    initialize()
    app.run(host="127.0.0.1", port=8000, threaded=True, debug=False)
