"""
ai_services.chatbot
---------------------
A small rule-based FAQ assistant for citizens. No paid API, no external
calls -- just keyword matching against a set of known intents, each with
a canned answer. Isolated behind `get_reply()` so it can be swapped for a
real LLM-backed chatbot later without touching any other code.
"""

from dataclasses import dataclass


@dataclass
class Intent:
    name: str
    keywords: list
    reply: str


INTENTS = [
    Intent(
        "greeting",
        ["hi", "hello", "hey", "namaste"],
        "Hi! I'm the CivicFix assistant. Ask me things like \"how do I check my complaint status\" "
        "or \"how do I report an issue\".",
    ),
    Intent(
        "check_status",
        ["status", "track", "where is my complaint", "progress"],
        "Go to Dashboard → My Complaints, then click on the complaint you want to check. "
        "You'll see its current status (Pending / In Progress / Resolved) and full history there.",
    ),
    Intent(
        "report_issue",
        ["report", "file a complaint", "submit", "how do i complain", "new complaint", "raise an issue"],
        "Click \"Report an Issue\" on your dashboard, fill in a title and description, drop a pin on the map "
        "for the location, and optionally attach a photo. You can leave the category on \"auto-detect\" "
        "and CivicFix will pick one for you.",
    ),
    Intent(
        "categories",
        ["category", "categories", "what can i report", "types of complaint", "kind of issue"],
        "CivicFix currently covers: Road Damage, Water Leakage, Garbage, Street Light, Drainage, and Others.",
    ),
    Intent(
        "sla_time",
        ["how long", "when will", "resolve", "eta", "time frame", "sla"],
        "Most complaints are reviewed within 48 hours. Anything flagged as an emergency gets a much shorter "
        "6-hour response window, and admins are automatically notified if a department falls behind.",
    ),
    Intent(
        "emergency",
        ["emergency", "urgent", "danger", "life threatening", "fire", "gas leak", "burst", "flooding", "flood"],
        "If this is a life-threatening emergency, please call your local emergency number right away. "
        "CivicFix speeds up non-emergency civic repairs -- but for anything dangerous right now, contact "
        "emergency services first, then file the complaint here for the record.",
    ),
    Intent(
        "contact_department",
        ["message", "contact", "talk to", "reach", "department reply", "hear back"],
        "CivicFix doesn't have a direct chat with departments. Instead, the department posts progress "
        "updates on your complaint's page, and the admin sends you a notification whenever your status changes.",
    ),
    Intent(
        "account_help",
        ["password", "login", "log in", "sign up", "register", "account", "forgot"],
        "You can register as a Citizen or Department Staff from the sign-up page. If you're stuck logging in, "
        "double-check your email and password -- there's no OTP step, it's a straight email + password login.",
    ),
    Intent(
        "thanks",
        ["thank", "thanks", "thank you", "appreciate"],
        "You're welcome! Let me know if there's anything else I can help with.",
    ),
]

FALLBACK_REPLY = (
    "I'm not sure about that one yet. Try asking about reporting an issue, checking your complaint status, "
    "response times, or how departments handle complaints. For anything else, check your complaint's "
    "detail page for the latest updates from the department."
)


def get_reply(message: str) -> str:
    """Returns the best-matching canned reply for the given message, or a fallback."""
    text = (message or "").lower()

    best_intent = None
    best_score = 0
    for intent in INTENTS:
        score = sum(1 for kw in intent.keywords if kw in text)
        if score > best_score:
            best_score = score
            best_intent = intent

    if best_intent:
        return best_intent.reply
    return FALLBACK_REPLY
