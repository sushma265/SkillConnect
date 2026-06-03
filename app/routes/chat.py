"""
SkillConnect – AI Chat Route
==============================
Provides a POST /chat/message endpoint that forwards user messages to
the Google Gemini API. Falls back to a built-in rule-based assistant
when no valid API key is configured, so the chatbot is always functional.
"""

from flask import Blueprint, request, jsonify
import os
import requests
import re

chat_bp = Blueprint("chat", __name__)

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

SYSTEM_PROMPT = """You are SkillBot, a friendly and knowledgeable AI assistant for SkillConnect — a professional event networking platform.

You help users with:
- Discovering and registering for events and workshops
- Understanding platform features (QR check-in, live polls, networking, Q&A)
- Getting advice on professional networking and skill development
- Navigating the SkillConnect dashboard as attendee or organizer
- Answering questions about sessions, speakers, and schedules

Keep responses concise, friendly, and helpful. Use bullet points for lists. If unsure about specific event details, guide users to browse the events page or contact the organizer. Always stay on topic related to SkillConnect and professional development."""

# ── Built-in fallback knowledge base ──────────────────────────────────────
_FALLBACK_QA = [
    (r"register|sign.?up|join.*event", (
        "To register for an event:\n"
        "1. Go to **Browse Events** from the navbar\n"
        "2. Click on any event you like\n"
        "3. Hit the **Register** button\n"
        "4. Free events confirm instantly! 🎉\n\n"
        "You can view all your registrations in **Dashboard → My Registrations**."
    )),
    (r"certif", (
        "Certificates are issued by event organizers after an event ends.\n\n"
        "- Once issued, they appear in **Dashboard → Certificates** tab\n"
        "- Each certificate has a unique verify link you can share\n"
        "- You can download or print your certificate from the certificate page"
    )),
    (r"qr|check.?in|checkin", (
        "**QR Check-In** lets you check into events easily:\n"
        "- Go to **Dashboard → My Registrations**\n"
        "- Click the **QR Code** button on your registration\n"
        "- Show the QR code to the event staff at the entrance ✅"
    )),
    (r"network|connect|connection", (
        "SkillConnect's networking features:\n"
        "- **Browse Events** and meet other attendees\n"
        "- Send connection requests from the event detail page\n"
        "- View your connections in **Dashboard → Connections**\n"
        "- Respond to requests in **Dashboard → Networking** tab"
    )),
    (r"poll|vote|survey", (
        "**Live Polls** let attendees vote during sessions:\n"
        "- Organizers create polls for specific sessions\n"
        "- You can vote in real-time during the event\n"
        "- Results are shown instantly to all attendees 📊"
    )),
    (r"session|talk|speaker|schedule", (
        "Sessions are individual talks/workshops within an event:\n"
        "- View sessions on the **Event Detail** page\n"
        "- Each session shows the speaker, time, and room\n"
        "- Organizers can add sessions from their dashboard"
    )),
    (r"dashboard|profile|account", (
        "Your **Dashboard** is your personal hub:\n"
        "- **My Registrations** – all events you've joined\n"
        "- **Connections** – your network\n"
        "- **Networking** – pending requests\n"
        "- **Certificates** – earned completion certificates\n"
        "- **(Organizers only)** My Events & Sessions"
    )),
    (r"organiz|create.?event|host", (
        "To become an **Organizer** and host events:\n"
        "1. Register with the **Organizer** role\n"
        "2. From Dashboard, click **Create Event**\n"
        "3. Fill in event details, date, capacity, and more\n"
        "4. Add sessions, polls, and announcements\n"
        "5. Issue certificates after the event ends 🏆"
    )),
    (r"virtual|online|zoom|meet", (
        "SkillConnect supports **virtual events**:\n"
        "- Toggle 'Virtual Event' when creating an event\n"
        "- Add your Zoom/Google Meet/Teams link\n"
        "- Registered attendees can access the meeting link from the event page"
    )),
    (r"payment|price|free|cost|fee", (
        "Event pricing on SkillConnect:\n"
        "- **Free events** – register instantly, no payment needed\n"
        "- **Paid events** – payment processed via Razorpay\n"
        "- Pricing is set by the event organizer\n"
        "- Check the event card for the price before registering"
    )),
    (r"hello|hi|hey|howdy|hola", (
        "Hi there! 👋 I'm **SkillBot**, your SkillConnect assistant!\n\n"
        "I can help you with:\n"
        "- 🗓️ Finding and registering for events\n"
        "- 🔗 Networking with attendees\n"
        "- 🏆 Understanding certificates\n"
        "- 📊 Using polls and Q&A\n\n"
        "What would you like to know?"
    )),
    (r"thank|thanks|great|awesome|perfect", (
        "You're welcome! 😊 Happy to help.\n"
        "Feel free to ask anything else about SkillConnect!"
    )),
    (r"what.*skillconnect|about.*platform|what.*(app|site|platform)", (
        "**SkillConnect** is a professional event networking platform where you can:\n\n"
        "- 🗓️ Discover and join events & workshops\n"
        "- 🔗 Network with professionals\n"
        "- 📊 Participate in live polls & Q&A\n"
        "- ✅ Check in with QR codes\n"
        "- 🏆 Earn completion certificates\n"
        "- 📢 Get event announcements\n\n"
        "Browse events at [/browse-events](/browse-events) to get started!"
    )),
    (r"analytic|stats|report|insight", (
        "**Analytics** (Organizers only):\n"
        "- View registration trends and check-in rates\n"
        "- Access from the navbar or Dashboard header\n"
        "- See session attendance and poll results"
    )),
]

_FALLBACK_DEFAULT = (
    "I'm SkillBot, your SkillConnect assistant! 🤖\n\n"
    "I can help you with events, registration, networking, certificates, QR check-in, and more.\n\n"
    "Try asking me:\n"
    "- *\"How do I register for an event?\"*\n"
    "- *\"Where are my certificates?\"*\n"
    "- *\"How does QR check-in work?\"*"
)


def _fallback_response(message: str) -> str:
    """Return a built-in rule-based response for the given message."""
    msg_lower = message.lower()
    for pattern, reply in _FALLBACK_QA:
        if re.search(pattern, msg_lower):
            return reply
    return _FALLBACK_DEFAULT


def _is_placeholder_key(key: str) -> bool:
    """Return True if the key is clearly a placeholder, not a real API key."""
    placeholders = {"your-gemini-api-key-here", "your_gemini_api_key", ""}
    return key.lower() in placeholders or "placeholder" in key.lower() or "your-" in key.lower()


@chat_bp.route("/message", methods=["POST"])
def send_message():
    """
    Accepts a JSON body:
        { "message": "user text", "history": [...] }
    Returns:
        { "reply": "assistant text" }

    Uses Gemini API if a valid key is configured, otherwise falls back
    to the built-in rule-based assistant.
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    api_key = os.getenv("GEMINI_API_KEY", "")

    # Use fallback if no valid API key
    if not api_key or _is_placeholder_key(api_key):
        return jsonify({"reply": _fallback_response(user_message), "source": "fallback"})

    # ── Try Gemini API ──────────────────────────────────────────────────
    contents = [
        {"role": "user",  "parts": [{"text": SYSTEM_PROMPT}]},
        {"role": "model", "parts": [{"text": "Understood! I'm SkillBot, ready to help you with SkillConnect. How can I assist you today?"}]},
    ]

    for turn in history[-10:]:
        role = "user" if turn.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": turn.get("text", "")}]})

    contents.append({"role": "user", "parts": [{"text": user_message}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 512,
            "topP": 0.9,
        },
    }

    try:
        resp = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json=payload,
            timeout=20,
            headers={"Content-Type": "application/json"},
        )

        # On 4xx errors fall back gracefully instead of showing an error
        if resp.status_code in (400, 401, 403):
            return jsonify({"reply": _fallback_response(user_message), "source": "fallback"})

        resp.raise_for_status()
        result = resp.json()

        candidates = result.get("candidates", [])
        if not candidates:
            return jsonify({"reply": _fallback_response(user_message), "source": "fallback"})

        parts = candidates[0].get("content", {}).get("parts", [])
        reply_text = " ".join(p.get("text", "") for p in parts).strip()

        if not reply_text:
            return jsonify({"reply": _fallback_response(user_message), "source": "fallback"})

        return jsonify({"reply": reply_text, "source": "gemini"})

    except requests.exceptions.Timeout:
        return jsonify({"reply": _fallback_response(user_message), "source": "fallback"})
    except Exception:
        return jsonify({"reply": _fallback_response(user_message), "source": "fallback"})
