from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import User, Course, Event, Payment
from app.utils import role_required

admin_bp = Blueprint("admin", __name__)


# ═══════════════════ USER MANAGEMENT ══════════════════════════════════════

# ── GET /admin/users ──────────────────────────────────────────────────────
@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_all_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200


# ── GET /admin/users/<id> ─────────────────────────────────────────────────
@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_user(user_id):
    user = User.query.get_or_404(user_id, description="User not found")
    return jsonify({"user": user.to_dict()}), 200


# ── PUT /admin/users/<id> ─────────────────────────────────────────────────
@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def update_user(user_id):
    user = User.query.get_or_404(user_id, description="User not found")
    data = request.get_json()

    if "role" in data:
        if data["role"] not in ("user", "conductor", "admin"):
            return jsonify({"error": "Invalid role"}), 400
        user.role = data["role"]

    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    if "name" in data:
        user.name = data["name"]

    db.session.commit()
    return jsonify({"message": "User updated", "user": user.to_dict()}), 200


# ── DELETE /admin/users/<id> ──────────────────────────────────────────────
@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id, description="User not found")
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200


# ═══════════════════ COURSE MANAGEMENT ════════════════════════════════════

# ── GET /admin/courses ────────────────────────────────────────────────────
@admin_bp.route("/courses", methods=["GET"])
@jwt_required()
@role_required("admin")
def admin_get_courses():
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return jsonify({"courses": [c.to_dict() for c in courses]}), 200


# ── DELETE /admin/courses/<id> ────────────────────────────────────────────
@admin_bp.route("/courses/<int:course_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def admin_delete_course(course_id):
    course = Course.query.get_or_404(course_id, description="Course not found")
    db.session.delete(course)
    db.session.commit()
    return jsonify({"message": "Course deleted by admin"}), 200


# ═══════════════════ EVENT MANAGEMENT ═════════════════════════════════════

# ── GET /admin/events ─────────────────────────────────────────────────────
@admin_bp.route("/events", methods=["GET"])
@jwt_required()
@role_required("admin")
def admin_get_events():
    events = Event.query.order_by(Event.event_date.asc()).all()
    return jsonify({"events": [e.to_dict() for e in events]}), 200


# ── DELETE /admin/events/<id> ─────────────────────────────────────────────
@admin_bp.route("/events/<int:event_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def admin_delete_event(event_id):
    event = Event.query.get_or_404(event_id, description="Event not found")
    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Event deleted by admin"}), 200


# ═══════════════════ PAYMENT MANAGEMENT ═══════════════════════════════════

# ── GET /admin/payments ───────────────────────────────────────────────────
@admin_bp.route("/payments", methods=["GET"])
@jwt_required()
@role_required("admin")
def admin_get_payments():
    status = request.args.get("status")   # ?status=paid
    query = Payment.query
    if status:
        query = query.filter_by(status=status)
    payments = query.order_by(Payment.created_at.desc()).all()
    total = sum(p.amount for p in payments if p.status == "paid")
    return jsonify({
        "payments": [p.to_dict() for p in payments],
        "total_revenue": total,
    }), 200
