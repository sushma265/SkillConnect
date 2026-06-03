"""
SkillConnect – Admin Routes
==============================
Platform administration: user management, event oversight,
organizer promotion, moderation, analytics, and platform controls.
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


# ─────────────────────────────────────────────────────────────
# USERS MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_users():
    """
    Get all users
    ---
    tags:
      - Admin Users
    security:
      - Bearer: []
    parameters:
      - name: role
        in: query
        type: string
        enum:
          - attendee
          - organizer
          - admin
    responses:
      200:
        description: Users fetched successfully
    """

    role = request.args.get("role")

    users = (
        User.objects(role=role).order_by("-created_at")
        if role
        else User.objects().order_by("-created_at")
    )

    return jsonify({
        "total": users.count(),
        "users": [user.to_dict() for user in users]
    }), 200


@admin_bp.route("/users/<user_id>", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_user(user_id):
    """
    Get single user details
    ---
    tags:
      - Admin Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: User details fetched
    """

    user = get_object_or_404(
        User,
        id=user_id,
        description="User not found"
    )

    return jsonify({
        "user": user.to_dict()
    }), 200


@admin_bp.route("/users/<user_id>/toggle-active", methods=["PUT"])
@jwt_required()
@role_required("admin")
def toggle_user_active(user_id):
    """
    Activate or deactivate user
    ---
    tags:
      - Admin Users
    security:
      - Bearer: []
    responses:
      200:
        description: User status updated
    """

    user = get_object_or_404(
        User,
        id=user_id,
        description="User not found"
    )

    user.is_active = not user.is_active
    user.save()

    status = "activated" if user.is_active else "deactivated"

    return jsonify({
        "message": f"User {status}",
        "user": user.to_dict()
    }), 200


@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def delete_user(user_id):
    """
    Delete user account
    ---
    tags:
      - Admin Users
    security:
      - Bearer: []
    responses:
      200:
        description: User deleted
    """

    user = get_object_or_404(
        User,
        id=user_id,
        description="User not found"
    )

    if user.role == "admin":
        return jsonify({
            "error": "Cannot delete admin user"
        }), 400

    user.delete()

    return jsonify({
        "message": "User deleted successfully"
    }), 200


# ─────────────────────────────────────────────────────────────
# ROLE MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_bp.route("/promote-organizer", methods=["PUT"])
@jwt_required()
@role_required("admin")
def promote_to_organizer():
    """
    Promote user to organizer
    ---
    tags:
      - Admin Roles
    security:
      - Bearer: []
    requestBody:
      required: true
    responses:
      200:
        description: User promoted
    """

    data = request.get_json()

    user_id = data.get("user_id")

    if not user_id:
        return jsonify({
            "error": "user_id is required"
        }), 400

    user = get_object_or_404(
        User,
        id=user_id,
        description="User not found"
    )

    if user.role == "admin":
        return jsonify({
            "error": "Cannot modify admin role"
        }), 400

    user.role = "organizer"
    user.save()

    return jsonify({
        "message": f"{user.name} promoted to organizer",
        "user": user.to_dict()
    }), 200


@admin_bp.route("/demote-user", methods=["PUT"])
@jwt_required()
@role_required("admin")
def demote_to_attendee():
    """
    Demote organizer to attendee
    ---
    tags:
      - Admin Roles
    security:
      - Bearer: []
    responses:
      200:
        description: User demoted
    """

    data = request.get_json()

    user_id = data.get("user_id")

    if not user_id:
        return jsonify({
            "error": "user_id is required"
        }), 400

    user = get_object_or_404(
        User,
        id=user_id,
        description="User not found"
    )

    if user.role == "admin":
        return jsonify({
            "error": "Cannot modify admin role"
        }), 400

    user.role = "attendee"
    user.save()

    return jsonify({
        "message": f"{user.name} demoted to attendee",
        "user": user.to_dict()
    }), 200


# ─────────────────────────────────────────────────────────────
# EVENTS MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_bp.route("/events", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_all_events():
    """
    Get all platform events
    ---
    tags:
      - Admin Events
    security:
      - Bearer: []
    responses:
      200:
        description: Events fetched successfully
    """

    events = Event.objects().order_by("-created_at")

    return jsonify({
        "total": events.count(),
        "events": [event.to_dict() for event in events]
    }), 200


@admin_bp.route("/events/<event_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def delete_event(event_id):
    """
    Delete event
    ---
    tags:
      - Admin Events
    security:
      - Bearer: []
    responses:
      200:
        description: Event deleted
    """

    event = get_object_or_404(
        Event,
        id=event_id,
        description="Event not found"
    )

    Registration.objects(event=event).delete()
    Question.objects(event=event).delete()
    PollVote.objects(event=event).delete()
    NetworkingRequest.objects(event=event).delete()
    Feedback.objects(event=event).delete()

    event.delete()

    return jsonify({
        "message": "Event deleted successfully"
    }), 200


# ─────────────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────────────

@admin_bp.route("/analytics", methods=["GET"])
@jwt_required()
@role_required("admin")
def platform_analytics():
    """
    Get platform analytics
    ---
    tags:
      - Admin Analytics
    security:
      - Bearer: []
    responses:
      200:
        description: Platform analytics
    """

    return jsonify(
        get_platform_analytics()
    ), 200


@admin_bp.route("/analytics/events/<event_id>", methods=["GET"])
@jwt_required()
@role_required("admin")
def event_analytics(event_id):
    """
    Get event analytics
    ---
    tags:
      - Admin Analytics
    security:
      - Bearer: []
    responses:
      200:
        description: Event analytics
    """

    event = get_object_or_404(
        Event,
        id=event_id,
        description="Event not found"
    )

    return jsonify(
        get_event_analytics(event)
    ), 200


@admin_bp.route("/analytics/participation", methods=["GET"])
@jwt_required()
@role_required("admin")
def participation_analytics():
    """
    Get participation analytics
    ---
    tags:
      - Admin Analytics
    security:
      - Bearer: []
    responses:
      200:
        description: Participation analytics
    """

    return jsonify({
        "events": get_participation_data()
    }), 200


# ─────────────────────────────────────────────────────────────
# DASHBOARD STATS
# ─────────────────────────────────────────────────────────────

@admin_bp.route("/dashboard/stats", methods=["GET"])
@jwt_required()
@role_required("admin")
def dashboard_stats():
    """
    Get dashboard statistics
    ---
    tags:
      - Admin Dashboard
    security:
      - Bearer: []
    responses:
      200:
        description: Dashboard statistics
    """

    total_users = User.objects.count()
    total_events = Event.objects.count()
    total_registrations = Registration.objects.count()
    total_feedbacks = Feedback.objects.count()

    organizers = User.objects(role="organizer").count()
    attendees = User.objects(role="attendee").count()

    active_events = Event.objects(status="active").count()

    return jsonify({
        "total_users": total_users,
        "total_events": total_events,
        "total_registrations": total_registrations,
        "total_feedbacks": total_feedbacks,
        "total_organizers": organizers,
        "total_attendees": attendees,
        "active_events": active_events
    }), 200


# ─────────────────────────────────────────────────────────────
# FEEDBACK MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_bp.route("/feedbacks", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_feedbacks():
    """
    Get all feedbacks
    ---
    tags:
      - Admin Feedback
    security:
      - Bearer: []
    responses:
      200:
        description: Feedback list
    """

    feedbacks = Feedback.objects().order_by("-created_at")

    return jsonify({
        "total": feedbacks.count(),
        "feedbacks": [f.to_dict() for f in feedbacks]
    }), 200


# ─────────────────────────────────────────────────────────────
# QUESTIONS MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_bp.route("/questions", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_questions():
    """
    Get all questions
    ---
    tags:
      - Admin Questions
    security:
      - Bearer: []
    responses:
      200:
        description: Questions fetched
    """

    questions = Question.objects().order_by("-created_at")

    return jsonify({
        "total": questions.count(),
        "questions": [q.to_dict() for q in questions]
    }), 200