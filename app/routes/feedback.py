"""
SkillConnect – Feedback Routes
=================================
Collect and display event/session feedback.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.models.feedback_model import Feedback
from app.models.event_model import Event
from app.models.session_model import Session
from app.utils.jwt_utils import get_current_user

feedback_bp = Blueprint("feedback", __name__)


# ── POST /feedback ──────────────────────────────────────────────────────
@feedback_bp.route("", methods=["POST"])
@jwt_required()
def submit_feedback():
    """
    Submit feedback for an event or session.
    ---
    tags: [Feedback]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [feedback_type, item_id, rating]
          properties:
            feedback_type: {type: string, enum: [event, session]}
            item_id:       {type: string}
            rating:        {type: integer, minimum: 1, maximum: 5}
            comment:       {type: string}
    responses:
      201: {description: Feedback submitted}
    """
    data = request.get_json()
    user = get_current_user()

    feedback_type = data.get("feedback_type")
    item_id = data.get("item_id")
    rating = data.get("rating")

    if feedback_type not in ("event", "session"):
        return jsonify({
            "error": "feedback_type must be 'event' or 'session'"
        }), 400

    if not item_id:
        return jsonify({"error": "item_id is required"}), 400

    if (
        rating is None
        or not isinstance(rating, int)
        or rating < 1
        or rating > 5
    ):
        return jsonify({
            "error": "rating must be an integer between 1 and 5"
        }), 400

    fb_kwargs = {
        "user": user,
        "rating": rating,
        "comment": data.get("comment"),
        "feedback_type": feedback_type,
    }

    if feedback_type == "event":
        item = Event.objects(id=item_id).first()
        if not item:
            return jsonify({"error": "Event not found"}), 404
        fb_kwargs["event"] = item
    else:
        item = Session.objects(id=item_id).first()
        if not item:
            return jsonify({"error": "Session not found"}), 404
        fb_kwargs["session"] = item

    fb = Feedback(**fb_kwargs)
    fb.save()

    return jsonify({
        "message": "Feedback submitted",
        "feedback": fb.to_dict(),
    }), 201


# ── GET /feedback ───────────────────────────────────────────────────────
@feedback_bp.route("", methods=["GET"])
def get_feedback():
    """
    Get feedback, optionally filtered by type and item.
    ---
    tags: [Feedback]
    parameters:
      - in: query
        name: type
        type: string
        enum: [event, session]
      - in: query
        name: item_id
        type: string
    responses:
      200: {description: Feedback list}
    """
    feedback_type = request.args.get("type")
    item_id = request.args.get("item_id")
    qs = Feedback.objects()

    if feedback_type in ("event", "session"):
        qs = qs.filter(feedback_type=feedback_type)

    if item_id and feedback_type == "event":
        item = Event.objects(id=item_id).first()
        if item:
            qs = qs.filter(event=item)
    elif item_id and feedback_type == "session":
        item = Session.objects(id=item_id).first()
        if item:
            qs = qs.filter(session=item)

    feedbacks = qs.order_by("-created_at")
    return jsonify({
        "feedback": [f.to_dict() for f in feedbacks]
    }), 200