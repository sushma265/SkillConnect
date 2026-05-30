from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Event, Registration
from app.utils import role_required, get_current_user

events_bp = Blueprint("events", __name__)

DATE_FMT = "%Y-%m-%d %H:%M"


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, DATE_FMT)
    except (ValueError, TypeError):
        return None


# ── POST /events  (conductor / admin) ────────────────────────────────────
@events_bp.route("", methods=["POST"])
@jwt_required()
@role_required("conductor", "admin")
def create_event():
    data = request.get_json()
    required = ["title", "description", "event_date"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    event_date = parse_date(data["event_date"])
    if not event_date:
        return jsonify({"error": "event_date must be in 'YYYY-MM-DD HH:MM' format"}), 400

    event_type = data.get("event_type", "event")
    if event_type not in ("event", "workshop"):
        return jsonify({"error": "event_type must be 'event' or 'workshop'"}), 400

    user_id = get_jwt_identity()
    event = Event(
        title=data["title"],
        description=data["description"],
        event_type=event_type,
        venue=data.get("venue"),
        event_date=event_date,
        price=float(data.get("price", 0)),
        capacity=int(data.get("capacity", 100)),
        created_by=int(user_id),
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({"message": "Event created", "event": event.to_dict()}), 201


# ── GET /events ────────────────────────────────────────────────────────────
@events_bp.route("", methods=["GET"])
def get_all_events():
    event_type = request.args.get("type")   # ?type=workshop
    query = Event.query
    if event_type:
        query = query.filter_by(event_type=event_type)
    events = query.order_by(Event.event_date.asc()).all()
    return jsonify({"events": [e.to_dict() for e in events]}), 200


# ── GET /events/<id> ───────────────────────────────────────────────────────
@events_bp.route("/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = Event.query.get_or_404(event_id, description="Event not found")
    return jsonify({"event": event.to_dict()}), 200


# ── PUT /events/<id> ──────────────────────────────────────────────────────
@events_bp.route("/<int:event_id>", methods=["PUT"])
@jwt_required()
@role_required("conductor", "admin")
def update_event(event_id):
    event = Event.query.get_or_404(event_id, description="Event not found")
    user = get_current_user()

    if user.role != "admin" and event.created_by != user.id:
        return jsonify({"error": "You can only update your own events"}), 403

    data = request.get_json()
    for field in ["title", "description", "venue", "event_type"]:
        if field in data:
            setattr(event, field, data[field])
    if "price" in data:
        event.price = float(data["price"])
    if "capacity" in data:
        event.capacity = int(data["capacity"])
    if "event_date" in data:
        parsed = parse_date(data["event_date"])
        if not parsed:
            return jsonify({"error": "event_date must be in 'YYYY-MM-DD HH:MM' format"}), 400
        event.event_date = parsed

    db.session.commit()
    return jsonify({"message": "Event updated", "event": event.to_dict()}), 200


# ── DELETE /events/<id> ───────────────────────────────────────────────────
@events_bp.route("/<int:event_id>", methods=["DELETE"])
@jwt_required()
@role_required("conductor", "admin")
def delete_event(event_id):
    event = Event.query.get_or_404(event_id, description="Event not found")
    user = get_current_user()

    if user.role != "admin" and event.created_by != user.id:
        return jsonify({"error": "You can only delete your own events"}), 403

    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Event deleted"}), 200


# ── POST /events/<id>/register ────────────────────────────────────────────
@events_bp.route("/<int:event_id>/register", methods=["POST"])
@jwt_required()
def register_for_event(event_id):
    event = Event.query.get_or_404(event_id, description="Event not found")
    user = get_current_user()

    # Already registered?
    existing = Registration.query.filter_by(
        user_id=user.id, event_id=event_id
    ).first()
    if existing:
        return jsonify({"error": "You are already registered for this event"}), 409

    # Capacity check
    confirmed_count = Registration.query.filter_by(
        event_id=event_id, status="confirmed"
    ).count()
    if confirmed_count >= event.capacity:
        return jsonify({"error": "Event is at full capacity"}), 400

    # Paid events → require payment first
    if event.price > 0:
        return jsonify({
            "message": "This is a paid event. Use POST /payments/create-order to register.",
            "event_id": event_id,
            "price": event.price,
        }), 200

    # Free event → register immediately
    reg = Registration(user_id=user.id, event_id=event_id, status="confirmed")
    db.session.add(reg)
    db.session.commit()
    return jsonify({"message": "Registered successfully", "registration": reg.to_dict()}), 201


# ── GET /my-registrations ─────────────────────────────────────────────────
@events_bp.route("/my-registrations", methods=["GET"])
@jwt_required()
def my_registrations():
    user = get_current_user()
    regs = Registration.query.filter_by(user_id=user.id).all()
    return jsonify({"registrations": [r.to_dict() for r in regs]}), 200
