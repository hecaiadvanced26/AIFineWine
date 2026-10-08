"""Deterministic guardrails around the model. The trust boundary lives in code, not in the prompt.

Layers: (1) screen_input before the model sees a message, (2) tool and SQL limits in the dispatcher
(catalog.py, tools.py, orders.py), (3) screen_output on every reply, (4) rate limits in server.py.
Pattern lists are a cheap first line: they catch known phrasings and are NOT a complete defence.
"""
import re

CANARY = "CVE-7f3a-91c4-canary"  # appears only in the system prompt; must never leave the server

CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
KEY_RE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|sk-or-[A-Za-z0-9_-]{8,}|OPENAI_API_KEY|OPENROUTER_API_KEY|FLASK_SECRET_KEY)\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
LEAK_RE = re.compile(r"run_query|recommend_wines|find_cheaper_alternatives|offer_choices|prepare_order|"
                     r"CREATE TABLE|\bSELECT\b[^.]{0,80}\bFROM\b|wine_pairings|flavour_vocabulary|"
                     r"catalog_metadata|sqlite_master|system prompt|my instructions say", re.I)
DISCOUNT_RE = re.compile(r"\d+\s?(?:%|percent)\s*(?:off|discount)|promo(?:tion(?:al)?)?\s*code|coupon|voucher|"
                         r"discount\s+(?:applied|code|of|granted)|(?:free|complimentary)\s+(?:bottle|shipping|delivery|gift)|"
                         r"price\s+(?:has been|was|is now)\s+(?:reduced|lowered|changed|set)|"
                         r"i(?:'ve| have)\s+(?:applied|added|granted)", re.I)
OVERRIDE_RE = re.compile(
    r"ignore\s+(?:all\s+|any\s+|your\s+|the\s+|my\s+|previous\s+|prior\s+|above\s+|earlier\s+)+"
    r"(?:instructions?|rules?|prompts?|guidelines?|messages?)|"
    r"disregard\s+(?:all\s+|your\s+|the\s+|previous\s+)+(?:instructions?|rules?|prompt)|"
    r"(?:reveal|show|print|repeat|output|display|leak|tell me)\s+(?:me\s+)?(?:your|the)\s+"
    r"(?:system\s+|hidden\s+|initial\s+|secret\s+)?(?:prompt|instructions?|rules|configuration)|"
    r"system\s+prompt|developer\s+mode|jailbreak|\bDAN\b|do anything now|"
    r"you\s+are\s+now\s+(?:a|an|the|in)\b|pretend\s+(?:to\s+be|you\s+are)|"
    r"(?:i\s+am|i'm|this\s+is|as)\s+(?:the\s+|your\s+|an?\s+)?(?:admin(?:istrator)?|supervisor|developer|root|operator)\b|"
    r"(?:i\s+am|i'm|this\s+is|as)\s+(?:the|your)\s+(?:manager|owner|engineer|staff|employee|ceo)\b|"
    r"(?:i\s+am|i'm)\s+(?:a\s+)?(?:staff|manager|employee|owner)\s+(?:of|at|from)\s+(?:this|the\s+shop|cave)|"
    r"(?:act|behave|respond)\s+as\s+(?:the\s+|a\s+|an\s+)?(?:admin|supervisor|manager|owner|developer|root|dan)|"
    r"</?(?:system|assistant|tool|instructions?)>|^\s*(?:system|assistant)\s*:", re.I | re.M)

REFUSAL = ("I can only help you find and choose a wine, so I can't do that. "
           "I also can't change prices or offer discounts: prices are exactly as shown on the cards. "
           "What are you in the mood for?")
CARD_REPLY = ("Please don't share card or payment details here. cave. takes no payments in this chat, "
              "and I never need them. Your message was not processed or stored. How can I help you find a wine?")
SAFE_REPLY = ("I can't help with that. I can help you find a wine, compare vintages or prepare an order draft. "
              "What would you like?")


def luhn_ok(digits):
    total, flip = 0, False
    for char in reversed(digits):
        number = int(char)
        if flip:
            number = number * 2 - 9 if number * 2 > 9 else number * 2
        total += number
        flip = not flip
    return total % 10 == 0


def has_card_number(text):
    for match in CARD_RE.finditer(text or ""):
        digits = re.sub(r"\D", "", match.group())
        if 13 <= len(digits) <= 19 and luhn_ok(digits):
            return True
    return False


def screen_input(text):
    """Return a canned reply when the message must not reach the model, otherwise None."""
    if has_card_number(text):
        return CARD_REPLY
    if OVERRIDE_RE.search(text or ""):
        return REFUSAL
    return None


def reply_problem(text, allowed_emails=()):
    """Name of the first rule a model reply breaks, or None."""
    text = text or ""
    if CANARY in text:
        return "canary"
    if has_card_number(text):
        return "card number"
    if KEY_RE.search(text):
        return "secret"
    if LEAK_RE.search(text):
        return "internal names"
    if DISCOUNT_RE.search(text):
        return "discount claim"
    allowed = {e.lower() for e in allowed_emails}
    if any(m.group().lower() not in allowed for m in EMAIL_RE.finditer(text)):
        return "unknown email"
    return None
