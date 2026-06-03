"""
SkillConnect – Event Routes
==============================
CRUD operations for events and event registration.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime

from app.models.event_model import Event
from app.models.registration_model import Registration
from app.utils.decorators import role_required
from app.utils.jwt_utils import get_current_user, get_object_or_404

events_bp = Blueprint("events", __name__)
DATE_FMT = "%Y-%m-%d %H:%M"


def _parse_date(s):
    """Parse a date string in 'YYYY-MM-DD HH:MM' format."""
    try:
        return datetime.strptime(s, DATE_FMT)
    except (ValueError, TypeError):
        return None


# ── POST /events ────────────────────────────────────────────────────────
@events_bp.route("", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def create_event():
    """
    Create a new event.
    ---
    tags: [Events]
    security: [{Bearer: []}]
    """
    data = request.get_json()

    for field in ["title", "description", "event_date"]:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    event_date = _parse_date(data["event_date"])
    if not event_date:
        return jsonify({
            "error": "event_date must be 'YYYY-MM-DD HH:MM'"
        }), 400

    event_type = data.get("event_type", "event")
    if event_type not in ("event", "workshop"):
        return jsonify({
            "error": "event_type must be 'event' or 'workshop'"
        }), 400

    end_date = None
    if data.get("end_date"):
        end_date = _parse_date(data["end_date"])

    user = get_current_user()
    ev = Event(
        title=data["title"],
        description=data["description"],
        event_type=event_type,
        venue=data.get("venue"),
        event_date=event_date,
        end_date=end_date,
        price=float(data.get("price", 0)),
        capacity=int(data.get("capacity", 100)),
        tags=data.get("tags", []),
        is_virtual=bool(data.get("is_virtual", False)),
        meeting_link=data.get("meeting_link"),
        banner_url=data.get("banner_url"),
        created_by=user,
    )
    ev.save()
    return jsonify({
        "message": "Event created",
        "event": ev.to_dict(),
    }), 201


# ── GET /events ─────────────────────────────────────────────────────────
@events_bp.route("", methods=["GET"])
def get_all_events():
    """
    Get all events, optionally filtered by type or search query.
    ---
    tags: [Events]
    """
    event_type = request.args.get("type")
    search = request.args.get("search", "").strip()

    qs = Event.objects()

    if event_type:
        qs = qs.filter(event_type=event_type)

    if search:
        qs = qs.filter(
            __raw__={
                "$or": [
                    {"title": {"$regex": search, "$options": "i"}},
                    {
                        "description": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                ]
            }
        )

    events = qs.order_by("event_date")
    return jsonify({
        "events": [e.to_dict() for e in events]
    }), 200


# ── GET /events/<id> ────────────────────────────────────────────────────
@events_bp.route("/<event_id>", methods=["GET"])
def get_event(event_id):
    """
    Get a single event by ID.
    ---
    tags: [Events]
    """
    ev = get_object_or_404(
        Event, id=event_id, description="Event not found"
    )
    return jsonify({"event": ev.to_dict()}), 200


# ── PUT /events/<id> ────────────────────────────────────────────────────
@events_bp.route("/<event_id>", methods=["PUT"])
@jwt_required()
@role_required("organizer", "admin")
def update_event(event_id):
    """
    Update an existing event.
    ---
    tags: [Events]
    security: [{Bearer: []}]
    """
    ev = get_object_or_404(
        Event, id=event_id, description="Event not found"
    )
    user = get_current_user()

    # Only the creator or admin can update
    if (
        user.role != "admin"
        and str(ev.created_by.id) != str(user.id)
    ):
        return jsonify({
            "error": "You can only update your own events"
        }), 403

    data = request.get_json()

    text_fields = [
        "title", "description", "venue", "event_type",
        "banner_url", "meeting_link",
    ]
    for field in text_fields:
        if field in data:
            setattr(ev, field, data[field])

    if "price" in data:
        ev.price = float(data["price"])
    if "capacity" in data:
        ev.capacity = int(data["capacity"])
    if "is_virtual" in data:
        ev.is_virtual = bool(data["is_virtual"])
    if "tags" in data:
        ev.tags = data["tags"]
    if "event_date" in data:
        parsed = _parse_date(data["event_date"])
        if not parsed:
            return jsonify({
                "error": "event_date must be 'YYYY-MM-DD HH:MM'"
            }), 400
        ev.event_date = parsed
    if "end_date" in data:
        parsed = _parse_date(data["end_date"])
        if parsed:
            ev.end_date = parsed

    ev.save()
    return jsonify({
        "message": "Event updated",
        "event": ev.to_dict(),
    }), 200


# ── DELETE /events/<id> ─────────────────────────────────────────────────
@events_bp.route("/<event_id>", methods=["DELETE"])
@jwt_required()
@role_required("organizer", "admin")
def delete_event(event_id):
    """
    Delete an event.
    ---
    tags: [Events]
    security: [{Bearer: []}]
    """
    ev = get_object_or_404(
        Event, id=event_id, description="Event not found"
    )
    user = get_current_user()

    if (
        user.role != "admin"
        and str(ev.created_by.id) != str(user.id)
    ):
        return jsonify({
            "error": "You can only delete your own events"
        }), 403

    ev.delete()
    return jsonify({"message": "Event deleted"}), 200


# ── POST /events/<id>/register ──────────────────────────────────────────
@events_bp.route("/<event_id>/register", methods=["POST"])
@jwt_required()
def register_for_event(event_id):
    """
    Register the current user for an event.
    ---
    tags: [Events]
    security: [{Bearer: []}]
    """
    ev = get_object_or_404(
        Event, id=event_id, description="Event not found"
    )
    user = get_current_user()

    # Check for existing registration
    existing = Registration.objects(user=user, event=ev).first()
    if existing:
        return jsonify({"error": "Already registered"}), 409

    # Check capacity
    confirmed = Registration.objects(
        event=ev, status="confirmed"
    ).count()
    if confirmed >= ev.capacity:
        return jsonify({
            "error": "Event is at full capacity"
        }), 400

    # Free event → auto-confirm
    reg = Registration(user=user, event=ev, status="confirmed")
    reg.generate_qr_token()
    reg.save()

    return jsonify({
        "message": "Registered successfully",
        "registration": reg.to_dict(),
    }), 201


# ── GET /events/my-registrations ────────────────────────────────────────
@events_bp.route("/my-registrations", methods=["GET"])
@jwt_required()
def my_registrations():
    """
    Get all event registrations for the current user.
    ---
    tags: [Events]
    security: [{Bearer: []}]
    """
    user = get_current_user()
    regs = Registration.objects(user=user).order_by("-registered_at")
    return jsonify({
        "registrations": [r.to_dict() for r in regs]
    }), 200


# ── GET /events/<id>/registrations ──────────────────────────────────────
@events_bp.route("/<event_id>/registrations", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def event_registrations(event_id):
    """
    Get all registrations for an event (organizer/admin only).
    ---
    tags: [Events]
    security: [{Bearer: []}]
    """
    ev = get_object_or_404(
        Event, id=event_id, description="Event not found"
    )
    regs = Registration.objects(event=ev).order_by("-registered_at")
    return jsonify({
        "total": regs.count(),
        "registrations": [r.to_dict() for r in regs],
    }), 200


# ── DELETE /events/<id> ─────────────────────────────────────────────────
@events_bp.route("/<event_id>", methods=["DELETE"])
@jwt_required()
def delete_event(event_id):
    """
    Delete an event (creator or admin only).
    Also removes all registrations linked to this event.
    ---
    tags: [Events]
    security: [{Bearer: []}]
    responses:
      200: {description: Event deleted}
      403: {description: Not authorised}
      404: {description: Event not found}
    """
    user = get_current_user()
    ev = get_object_or_404(Event, id=event_id, description="Event not found")

    # Only the creator or an admin may delete
    if str(ev.created_by.id) != str(user.id) and user.role != "admin":
        return jsonify({"error": "You are not authorised to delete this event"}), 403

    # Cascade-delete all registrations for this event
    deleted_regs = Registration.objects(event=ev).count()
    Registration.objects(event=ev).delete()

    title = ev.title
    ev.delete()

    return jsonify({
        "message": f'Event "{title}" deleted successfully',
        "registrations_removed": deleted_regs,
    }), 200