"""
SkillConnect – AI Chat Routes
================================
Advanced AI assistant system with:
- Gemini AI integration
- Smart fallback chatbot
- Conversation history
- Suggested prompts
- Event assistance
- Networking guidance
- FAQ support
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import requests
import os
import re

chat_bp = Blueprint(
    "chat",
    __name__
)


# ═════════════════════════════════════════════════════════════
# GEMINI CONFIG
# ═════════════════════════════════════════════════════════════

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

SYSTEM_PROMPT = """
You are SkillBot, the AI assistant of SkillConnect.

Your responsibilities:
- Help users discover events
- Explain platform features
- Guide organizers
- Help with networking
- Answer FAQs
- Provide professional development advice

Always:
- Be concise
- Friendly
- Professional
- Helpful
- Use bullet points when useful
- Stay focused on SkillConnect
"""


# ═════════════════════════════════════════════════════════════
# FALLBACK KNOWLEDGE BASE
# ═════════════════════════════════════════════════════════════

FALLBACK_QA = [

    (
        r"register|join|signup|sign.?up",
        (
            "To register for an event:\n\n"
            "1. Browse available events\n"
            "2. Open the event page\n"
            "3. Click Register\n"
            "4. Complete registration\n\n"
            "Your registrations appear in Dashboard."
        )
    ),

    (
        r"certificate|certificates",
        (
            "Certificates are issued by organizers after events.\n\n"
            "- View them in Dashboard → Certificates\n"
            "- Each certificate includes verification\n"
            "- Certificates can be downloaded and shared"
        )
    ),

    (
        r"qr|checkin|check.?in",
        (
            "QR Check-In allows fast event entry.\n\n"
            "- Open Dashboard → My Registrations\n"
            "- Click QR Code\n"
            "- Show it at the event entrance"
        )
    ),

    (
        r"network|connect|connection",
        (
            "Networking features include:\n\n"
            "- Connection requests\n"
            "- Professional networking\n"
            "- Attendee discovery\n"
            "- Event networking dashboard"
        )
    ),

    (
        r"poll|vote",
        (
            "Live Polls help attendees interact during sessions.\n\n"
            "- Vote in real-time\n"
            "- See instant results\n"
            "- Participate from event pages"
        )
    ),

    (
        r"analytics|report|stats",
        (
            "Analytics features include:\n\n"
            "- Registration tracking\n"
            "- Attendance rates\n"
            "- Check-in insights\n"
            "- Event performance reports"
        )
    ),

    (
        r"hello|hi|hey",
        (
            "Hello! 👋 I'm SkillBot.\n\n"
            "I can help with:\n"
            "- Events\n"
            "- Registration\n"
            "- Certificates\n"
            "- Networking\n"
            "- QR Check-In\n"
            "- Analytics"
        )
    ),

]


DEFAULT_RESPONSE = (
    "I'm SkillBot 🤖\n\n"
    "I can help you with:\n"
    "- Event registration\n"
    "- Networking\n"
    "- Certificates\n"
    "- QR check-in\n"
    "- Analytics\n"
    "- Organizer tools\n\n"
    "Ask me anything about SkillConnect!"
)


# ═════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═════════════════════════════════════════════════════════════

def fallback_response(message):

    msg = message.lower()

    for pattern, reply in FALLBACK_QA:

        if re.search(pattern, msg):
            return reply

    return DEFAULT_RESPONSE


def is_placeholder_key(key):

    placeholders = [
        "",
        "your-gemini-api-key",
        "your_gemini_api_key",
        "placeholder"
    ]

    key_lower = key.lower()

    return (
        key_lower in placeholders
        or "your-" in key_lower
        or "placeholder" in key_lower
    )


# ═════════════════════════════════════════════════════════════
# CHAT MESSAGE ENDPOINT
# ═════════════════════════════════════════════════════════════

@chat_bp.route("/message", methods=["POST"])
def send_message():
    """
    Send message to AI chatbot
    ---
    tags:
      - AI Chatbot
    consumes:
      - application/json
    responses:
      200:
        description: AI response
    """

    data = request.get_json(
        silent=True
    ) or {}

    user_message = (
        data.get("message", "")
        .strip()
    )

    history = data.get(
        "history",
        []
    )

    if not user_message:
        return jsonify({
            "error":
                "Message cannot be empty"
        }), 400

    api_key = os.getenv(
        "GEMINI_API_KEY",
        ""
    )

    # ─────────────────────────────────────────
    # FALLBACK CHATBOT
    # ─────────────────────────────────────────

    if (
        not api_key
        or is_placeholder_key(api_key)
    ):

        return jsonify({
            "reply":
                fallback_response(
                    user_message
                ),

            "source":
                "fallback",

            "timestamp":
                datetime.utcnow().isoformat()
        }), 200

    # ─────────────────────────────────────────
    # GEMINI AI
    # ─────────────────────────────────────────

    contents = [

        {
            "role": "user",
            "parts": [
                {
                    "text": SYSTEM_PROMPT
                }
            ]
        },

        {
            "role": "model",
            "parts": [
                {
                    "text":
                        "Understood! "
                        "I am SkillBot."
                }
            ]
        }

    ]

    # Add recent history

    for turn in history[-10:]:

        role = (
            "user"
            if turn.get("role") == "user"
            else "model"
        )

        contents.append({
            "role": role,
            "parts": [
                {
                    "text":
                        turn.get("text", "")
                }
            ]
        })

    contents.append({
        "role": "user",
        "parts": [
            {
                "text": user_message
            }
        ]
    })

    payload = {

        "contents": contents,

        "generationConfig": {

            "temperature": 0.7,

            "maxOutputTokens": 512,

            "topP": 0.9,

        },
    }

    try:

        response = requests.post(

            f"{GEMINI_API_URL}?key={api_key}",

            json=payload,

            timeout=20,

            headers={
                "Content-Type":
                    "application/json"
            },
        )

        # Invalid API key → fallback

        if response.status_code in (
            400,
            401,
            403
        ):

            return jsonify({

                "reply":
                    fallback_response(
                        user_message
                    ),

                "source":
                    "fallback"

            }), 200

        response.raise_for_status()

        result = response.json()

        candidates = result.get(
            "candidates",
            []
        )

        if not candidates:

            return jsonify({

                "reply":
                    fallback_response(
                        user_message
                    ),

                "source":
                    "fallback"

            }), 200

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        reply_text = " ".join(
            p.get("text", "")
            for p in parts
        ).strip()

        if not reply_text:

            reply_text = fallback_response(
                user_message
            )

            source = "fallback"

        else:

            source = "gemini"

        return jsonify({

            "reply": reply_text,

            "source": source,

            "timestamp":
                datetime.utcnow().isoformat()

        }), 200

    except requests.exceptions.Timeout:

        return jsonify({

            "reply":
                fallback_response(
                    user_message
                ),

            "source":
                "fallback",

            "error":
                "Gemini timeout"

        }), 200

    except Exception as e:

        return jsonify({

            "reply":
                fallback_response(
                    user_message
                ),

            "source":
                "fallback",

            "error": str(e)

        }), 200


# ═════════════════════════════════════════════════════════════
# CHAT HEALTH CHECK
# ═════════════════════════════════════════════════════════════

@chat_bp.route("/health", methods=["GET"])
def chatbot_health():
    """
    Chatbot health status
    ---
    tags:
      - AI Chatbot
    """

    api_key = os.getenv(
        "GEMINI_API_KEY",
        ""
    )

    ai_enabled = (
        bool(api_key)
        and not is_placeholder_key(api_key)
    )

    return jsonify({

        "status": "online",

        "ai_enabled": ai_enabled,

        "provider":
            "Gemini"
            if ai_enabled
            else "Fallback AI",

        "chatbot_name":
            "SkillBot"

    }), 200


# ═════════════════════════════════════════════════════════════
# SUGGESTED PROMPTS
# ═════════════════════════════════════════════════════════════

@chat_bp.route("/suggestions", methods=["GET"])
def suggested_prompts():
    """
    Suggested chatbot prompts
    ---
    tags:
      - AI Chatbot
    """

    suggestions = [

        "How do I register for an event?",

        "Where can I find my certificates?",

        "How does QR check-in work?",

        "How can I become an organizer?",

        "How do live polls work?",

        "How can I network with attendees?",

        "How do analytics work?",

        "Can I host virtual events?",

    ]

    return jsonify({
        "suggestions": suggestions
    }), 200