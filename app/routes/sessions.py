"""
SkillConnect – Session Routes
================================
CRUD operations for event sessions.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime

from app.models.session_model import Session
from app.models.event_model import Event
from app.utils.decorators import role_required
from app.utils.jwt_utils import get_current_user, get_object_or_404

sessions_bp = Blueprint("sessions", __name__)
DATE_FMT = "%Y-%m-%d %H:%M"
SESSION_TYPES = ("keynote", "panel", "workshop", "networking", "break")


def _parse_dt(s):
    """Parse a datetime string."""
    try:
        return datetime.strptime(s, DATE_FMT)
    except (ValueError, TypeError):
        return None


# ── POST /sessions ──────────────────────────────────────────────────────
@sessions_bp.route("", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def create_session():
    """
    Create a new session within an event.
    ---
    tags: [Sessions]
    security: [{Bearer: []}]
    """
    data = request.get_json()

    for field in ["event_id", "title", "starts_at", "ends_at"]:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    event = get_object_or_404(
        Event, id=data["event_id"], description="Event not found"
    )

    starts_at = _parse_dt(data["starts_at"])
    ends_at = _parse_dt(data["ends_at"])
    if not starts_at or not ends_at:
        return jsonify({
            "error": "starts_at and ends_at must be 'YYYY-MM-DD HH:MM'"
        }), 400

    if ends_at <= starts_at:
        return jsonify({
            "error": "ends_at must be after starts_at"
        }), 400

    session_type = data.get("session_type", "keynote")
    if session_type not in SESSION_TYPES:
        return jsonify({
            "error": f"session_type must be one of {SESSION_TYPES}"
        }), 400

    user = get_current_user()
    s = Session(
        event=event,
        title=data["title"],
        description=data.get("description"),
        speaker_name=data.get("speaker_name"),
        speaker_bio=data.get("speaker_bio"),
        speaker_avatar_url=data.get("speaker_avatar_url"),
        session_type=session_type,
        room=data.get("room"),
        starts_at=starts_at,
        ends_at=ends_at,
        is_live=bool(data.get("is_live", False)),
        stream_url=data.get("stream_url"),
        created_by=user,
    )
    s.save()
    return jsonify({
        "message": "Session created",
        "session": s.to_dict(),
    }), 201


# ── GET /sessions ───────────────────────────────────────────────────────
@sessions_bp.route("", methods=["GET"])
def list_sessions():
    """
    List sessions, optionally filtered by event_id or session_type.
    ---
    tags: [Sessions]
    """
    qs = Session.objects()

    if request.args.get("event_id"):
        event = Event.objects(id=request.args["event_id"]).first()
        if event:
            qs = qs.filter(event=event)

    if request.args.get("session_type"):
        qs = qs.filter(session_type=request.args["session_type"])

    sessions = qs.order_by("starts_at")
    return jsonify({
        "sessions": [s.to_dict() for s in sessions]
    }), 200


# ── GET /sessions/<id> ──────────────────────────────────────────────────
@sessions_bp.route("/<session_id>", methods=["GET"])
def get_session(session_id):
    """
    Get a single session by ID.
    ---
    tags: [Sessions]
    """
    s = get_object_or_404(
        Session, id=session_id, description="Session not found"
    )
    return jsonify({"session": s.to_dict()}), 200


# ── PUT /sessions/<id> ──────────────────────────────────────────────────
@sessions_bp.route("/<session_id>", methods=["PUT"])
@jwt_required()
@role_required("organizer", "admin")
def update_session(session_id):
    """
    Update a session.
    ---
    tags: [Sessions]
    security: [{Bearer: []}]
    """
    s = get_object_or_404(
        Session, id=session_id, description="Session not found"
    )
    user = get_current_user()

    if (
        user.role != "admin"
        and str(s.created_by.id) != str(user.id)
    ):
        return jsonify({
            "error": "You can only update your own sessions"
        }), 403

    data = request.get_json()

    text_fields = [
        "title", "description", "speaker_name", "speaker_bio",
        "speaker_avatar_url", "room", "stream_url",
    ]
    for field in text_fields:
        if field in data:
            setattr(s, field, data[field])

    if "session_type" in data:
        if data["session_type"] not in SESSION_TYPES:
            return jsonify({
                "error": f"session_type must be one of {SESSION_TYPES}"
            }), 400
        s.session_type = data["session_type"]

    if "is_live" in data:
        s.is_live = bool(data["is_live"])

    if "starts_at" in data:
        parsed = _parse_dt(data["starts_at"])
        if not parsed:
            return jsonify({
                "error": "starts_at must be 'YYYY-MM-DD HH:MM'"
            }), 400
        s.starts_at = parsed

    if "ends_at" in data:
        parsed = _parse_dt(data["ends_at"])
        if not parsed:
            return jsonify({
                "error": "ends_at must be 'YYYY-MM-DD HH:MM'"
            }), 400
        s.ends_at = parsed

    s.save()
    return jsonify({
        "message": "Session updated",
        "session": s.to_dict(),
    }), 200


# ── DELETE /sessions/<id> ───────────────────────────────────────────────
@sessions_bp.route("/<session_id>", methods=["DELETE"])
@jwt_required()
@role_required("organizer", "admin")
def delete_session(session_id):
    """
    Delete a session.
    ---
    tags: [Sessions]
    security: [{Bearer: []}]
    """
    s = get_object_or_404(
        Session, id=session_id, description="Session not found"
    )
    user = get_current_user()

    if (
        user.role != "admin"
        and str(s.created_by.id) != str(user.id)
    ):
        return jsonify({
            "error": "You can only delete your own sessions"
        }), 403

    s.delete()
    return jsonify({"message": "Session deleted"}), 200
