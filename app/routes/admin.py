"""
SkillConnect – Admin Routes
==============================
Platform administration: user management, event oversight,
organizer promotion, and platform-wide analytics.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.models.user_model import User
from app.models.event_model import Event
from app.models.registration_model import Registration
from app.models.question_model import Question
from app.models.poll_model import PollVote
from app.models.networking_model import NetworkingRequest
from app.models.feedback_model import Feedback
from app.utils.decorators import role_required
from app.utils.jwt_utils import get_object_or_404
from app.utils.analytics_utils import (
    get_platform_analytics,
    get_event_analytics,
    get_participation_data,
)

admin_bp = Blueprint("admin", __name__)


# ── GET /admin/users ────────────────────────────────────────────────────
@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_users():
    """
    Get all users, optionally filtered by role.
    ---
    tags: [Admin]
    security: [{Bearer: []}]
    parameters:
      - in: query
        name: role
        type: string
        enum: [attendee, organizer, admin]
    responses:
      200: {description: User list}
    """
    role = request.args.get("role")
    qs = User.objects(role=role) if role else User.objects()
    users = qs.order_by("-created_at")
    return jsonify({
        "total": users.count(),
        "users": [u.to_dict() for u in users],
    }), 200


# ── GET /admin/users/<user_id> ──────────────────────────────────────────
@admin_bp.route("/users/<user_id>", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_user(user_id):
    """
    Get a user's full details (admin only).
    ---
    tags: [Admin]
    security: [{Bearer: []}]
    """
    user = get_object_or_404(
        User, id=user_id, description="User not found"
    )
    return jsonify({"user": user.to_dict()}), 200


# ── PUT /admin/users/<user_id>/toggle-active ────────────────────────────
@admin_bp.route("/users/<user_id>/toggle-active", methods=["PUT"])
@jwt_required()
@role_required("admin")
def toggle_user_active(user_id):
    """
    Activate or deactivate a user account.
    ---
    tags: [Admin]
    security: [{Bearer: []}]
    """
    user = get_object_or_404(
        User, id=user_id, description="User not found"
    )
    user.is_active = not user.is_active
    user.save()

    status = "activated" if user.is_active else "deactivated"
    return jsonify({
        "message": f"User {status}",
        "user": user.to_dict(),
    }), 200


# ── PUT /admin/promote-organizer ────────────────────────────────────────
@admin_bp.route("/promote-organizer", methods=["PUT"])
@jwt_required()
@role_required("admin")
def promote_to_organizer():
    """
    Promote a user to organizer role.
    ---
    tags: [Admin]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [user_id]
          properties:
            user_id: {type: string}
    responses:
      200: {description: User promoted}
    """
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    user = get_object_or_404(
        User, id=user_id, description="User not found"
    )

    if user.role == "admin":
        return jsonify({
            "error": "Cannot change admin role"
        }), 400

    user.role = "organizer"
    user.save()

    return jsonify({
        "message": f"{user.name} promoted to organizer",
        "user": user.to_dict(),
    }), 200


# ── PUT /admin/demote-user ─────────────────────────────────────────────
@admin_bp.route("/demote-user", methods=["PUT"])
@jwt_required()
@role_required("admin")
def demote_to_attendee():
    """
    Demote an organizer back to attendee.
    ---
    tags: [Admin]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [user_id]
          properties:
            user_id: {type: string}
    responses:
      200: {description: User demoted}
    """
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    user = get_object_or_404(
        User, id=user_id, description="User not found"
    )

    if user.role == "admin":
        return jsonify({
            "error": "Cannot change admin role"
        }), 400

    user.role = "attendee"
    user.save()

    return jsonify({
        "message": f"{user.name} demoted to attendee",
        "user": user.to_dict(),
    }), 200


# ── GET /admin/events ──────────────────────────────────────────────────
@admin_bp.route("/events", methods=["GET"])
@jwt_required()
@role_required("admin")
def admin_events():
    """
    Get all events (admin view).
    ---
    tags: [Admin]
    security: [{Bearer: []}]
    """
    events = Event.objects().order_by("-created_at")
    return jsonify({
        "total": events.count(),
        "events": [e.to_dict() for e in events],
    }), 200


# ── DELETE /admin/events/<event_id> ─────────────────────────────────────
@admin_bp.route("/events/<event_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def admin_delete_event(event_id):
    """
    Force-delete an event (admin only).
    ---
    tags: [Admin]
    security: [{Bearer: []}]
    """
    event = get_object_or_404(
        Event, id=event_id, description="Event not found"
    )
    # Cascade delete registrations
    Registration.objects(event=event).delete()
    event.delete()
    return jsonify({"message": "Event deleted by admin"}), 200


# ── GET /admin/analytics ───────────────────────────────────────────────
@admin_bp.route("/analytics", methods=["GET"])
@jwt_required()
@role_required("admin")
def admin_analytics():
    """
    Get platform-wide analytics (admin only).
    ---
    tags: [Admin]
    security: [{Bearer: []}]
    """
    return jsonify(get_platform_analytics()), 200


# ── GET /admin/analytics/events/<event_id> ──────────────────────────────
@admin_bp.route("/analytics/events/<event_id>", methods=["GET"])
@jwt_required()
@role_required("admin")
def admin_event_analytics(event_id):
    """
    Get per-event analytics (admin only).
    ---
    tags: [Admin]
    security: [{Bearer: []}]
    """
    event = get_object_or_404(
        Event, id=event_id, description="Event not found"
    )
    return jsonify(get_event_analytics(event)), 200


# ── GET /admin/analytics/participation ──────────────────────────────────
@admin_bp.route("/analytics/participation", methods=["GET"])
@jwt_required()
@role_required("admin")
def admin_participation():
    """
    Get participation rates across all events.
    ---
    tags: [Admin]
    security: [{Bearer: []}]
    """
    return jsonify({"events": get_participation_data()}), 200