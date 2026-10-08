"""Browser chat: the same agent, with streamed text and real activity updates."""
import os
import sqlite3

import streamlit as st
from openai import OpenAI

from agent import chat
from database import initialize
from memory import Memory
from orders import submit_order

st.set_page_config(page_title="Wine assistant", page_icon="🍷", layout="centered")
st.title("Wine assistant")
st.caption("Find a bottle. Ask a question. Review your order.")
st.caption("Demo catalog · Search by price, vintage or available quantity. Local orders only.")

key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL")
if not key or not model:
    st.error("Missing API settings. Add them to .env, then run ./start.sh.")
    st.stop()

if "memory" not in st.session_state:
    try:
        initialize()
    except (OSError, sqlite3.Error):
        st.error("Catalog could not be loaded. Check the local data folder and restart.")
        st.stop()
    st.session_state.memory = Memory()
    st.session_state.history = []

memory = st.session_state.memory
history = st.session_state.history


def save_action(request, reply):
    """Keep button actions in both displayed history and the model's memory."""
    memory.start_turn(request)
    memory.add_reply(reply)
    history.extend([{"role": "user", "content": request},
                    {"role": "assistant", "content": reply}])


if st.button("New conversation"):
    st.session_state.memory = Memory()
    st.session_state.history = []
    st.rerun()

if not history:
    st.info('Try: “Show available wines under €20 with at least 2 bottles in stock.”')
for message in history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

text = st.chat_input("Ask about price, vintage, stock or a specific wine…")
if text and text.strip():
    history.append({"role": "user", "content": text})
    with st.chat_message("user"):
        st.markdown(text)
    with st.chat_message("assistant"):
        activity = st.status("Starting request…", expanded=False)
        output = st.empty()
        fragments = []
        events = []

        def show_text(fragment):
            fragments.append(fragment)
            output.markdown("".join(fragments))

        def show_status(label):
            events.append(label)
            activity.update(label=label)
            activity.write(label)

        client = OpenAI(api_key=key, base_url=os.getenv("OPENAI_BASE_URL") or None,
                        timeout=30, max_retries=1)
        reply = chat(client, model, memory, text, on_text=show_text,
                     on_status=show_status)
        output.markdown(reply)
        complete = bool(events) and events[-1] == "Reply complete."
        activity.update(state="complete" if complete else "error")
    history.append({"role": "assistant", "content": reply})

order_panel = st.container()
if memory.pending_order:
    with order_panel:
        draft = memory.pending_order
        with st.container(border=True):
            st.subheader("Review order")
            st.write(f"{draft['quantity']} × {draft['name']} ({draft['wine_id']})")
            st.write(f"Vintage: {draft['vintage'] or 'Not specified'} · "
                     f"Total: €{draft['total_cents'] / 100:.2f}")
            st.caption("Confirm exports a local demo order, not a payment or shop submission. "
                       "Sending another message discards this draft.")
            confirm, cancel = st.columns(2)
            if confirm.button("Confirm order", type="primary", use_container_width=True):
                with st.status("Rechecking stock and exporting order…") as activity:
                    try:
                        result = submit_order(draft)
                    except (OSError, sqlite3.Error):
                        activity.update(label="Export failed — retry with the same order ID.",
                                        state="error")
                        st.error("Draft retained. Retry Confirm order; duplicate stock changes "
                                 "are prevented.")
                    else:
                        memory.pending_order = None
                        reply = (result["error"] if result.get("error") else
                                 f"Order {result['order_id']} exported locally. No payment taken.")
                        save_action("Confirm order", reply)
                        st.rerun()
            if cancel.button("Cancel order", use_container_width=True):
                memory.pending_order = None
                save_action("Cancel order", "Order draft cancelled. Nothing was submitted.")
                st.rerun()
