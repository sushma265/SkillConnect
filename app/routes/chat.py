"""
SkillConnect – AI Chat Route
==============================
Provides a POST /chat/message endpoint that forwards user messages to
the Google Gemini API and streams back the assistant response.
The system prompt anchors Gemini as a SkillConnect event assistant.
"""

from flask import Blueprint, request, jsonify
import os
import requests

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


@chat_bp.route("/message", methods=["POST"])
def send_message():
    """
    Accepts a JSON body with:
        {
            "message": "user text",
            "history": [ {"role": "user"|"model", "text": "..."}, ... ]
        }
    Returns:
        { "reply": "assistant text" }
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return jsonify({"error": "AI service is not configured."}), 503

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    # Build Gemini contents array
    contents = []

    # Inject system prompt as first user turn (Gemini doesn't have a system role)
    contents.append({
        "role": "user",
        "parts": [{"text": SYSTEM_PROMPT}]
    })
    contents.append({
        "role": "model",
        "parts": [{"text": "Understood! I'm SkillBot, ready to help you with SkillConnect. How can I assist you today?"}]
    })

    # Add conversation history
    for turn in history[-10:]:  # Keep last 10 turns to avoid token limits
        role = "user" if turn.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": turn.get("text", "")}]
        })

    # Add the new user message
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 512,
            "topP": 0.9,
        }
    }

    try:
        resp = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json=payload,
            timeout=20,
            headers={"Content-Type": "application/json"}
        )
        resp.raise_for_status()
        result = resp.json()

        # Extract text from Gemini response
        candidates = result.get("candidates", [])
        if not candidates:
            return jsonify({"error": "No response from AI."}), 502

        parts = candidates[0].get("content", {}).get("parts", [])
        reply_text = " ".join(p.get("text", "") for p in parts).strip()

        return jsonify({"reply": reply_text})

    except requests.exceptions.Timeout:
        return jsonify({"error": "AI response timed out. Please try again."}), 504
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 500
        if status == 400:
            return jsonify({"error": "Invalid request to AI service."}), 400
        if status == 403:
            return jsonify({"error": "AI service authentication failed. Check your API key."}), 503
        return jsonify({"error": "AI service error."}), 502
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
