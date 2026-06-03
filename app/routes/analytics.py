"""
SkillConnect – Analytics & Check-In Routes
===========================================
Advanced analytics dashboard, QR attendance tracking,
event insights, reports, and Chart.js compatible APIs.
"""

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from datetime import datetime, timezone
import io

from app.models.registration_model import Registration
from app.models.event_model import Event
from app.models.user_model import User
from app.models.feedback_model import Feedback
from app.models.question_model import Question

from app.utils.decorators import role_required
from app.utils.jwt_utils import get_current_user, get_object_or_404

from app.utils.analytics_utils import (
    get_platform_analytics,
    get_event_analytics,
    get_participation_data,
)

from app.utils.qr_utils import generate_qr_image

analytics_bp = Blueprint("analytics", __name__)

# ─────────────────────────────────────────────────────────────
# QR CACHE
# ─────────────────────────────────────────────────────────────

_qr_cache = {}

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False


# ═════════════════════════════════════════════════════════════
# DASHBOARD ANALYTICS
# ═════════════════════════════════════════════════════════════

@analytics_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def dashboard():
    """
    Get dashboard analytics
    ---
    tags:
      - Analytics Dashboard
    security:
      - Bearer: []
    responses:
      200:
        description: Dashboard analytics
    """

    return jsonify(
        get_platform_analytics()
    ), 200


@analytics_bp.route("/events/<event_id>", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def event_analytics(event_id):
    """
    Get event analytics
    ---
    tags:
      - Analytics Dashboard
    security:
      - Bearer: []
    parameters:
      - name: event_id
        in: path
        type: string
        required: true
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


@analytics_bp.route("/participation", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def participation():
    """
    Get participation analytics
    ---
    tags:
      - Analytics Dashboard
    security:
      - Bearer: []
    responses:
      200:
        description: Participation analytics
    """

    return jsonify({
        "events": get_participation_data()
    }), 200


# ═════════════════════════════════════════════════════════════
# CHART DATA APIs
# ═════════════════════════════════════════════════════════════

@analytics_bp.route("/charts/users-by-role", methods=["GET"])
@jwt_required()
@role_required("admin")
def users_by_role():
    """
    Users grouped by role
    ---
    tags:
      - Analytics Charts
    security:
      - Bearer: []
    """

    attendees = User.objects(role="attendee").count()
    organizers = User.objects(role="organizer").count()
    admins = User.objects(role="admin").count()

    return jsonify({
        "labels": ["Attendees", "Organizers", "Admins"],
        "datasets": [
            {
                "label": "Users",
                "data": [attendees, organizers, admins]
            }
        ]
    }), 200


@analytics_bp.route("/charts/event-status", methods=["GET"])
@jwt_required()
@role_required("admin")
def event_status_chart():
    """
    Event status analytics
    ---
    tags:
      - Analytics Charts
    security:
      - Bearer: []
    """

    active = Event.objects(status="active").count()
    completed = Event.objects(status="completed").count()
    cancelled = Event.objects(status="cancelled").count()

    return jsonify({
        "labels": ["Active", "Completed", "Cancelled"],
        "datasets": [
            {
                "label": "Events",
                "data": [active, completed, cancelled]
            }
        ]
    }), 200


@analytics_bp.route("/charts/checkins/<event_id>", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def checkin_chart(event_id):
    """
    Check-in statistics chart
    ---
    tags:
      - Analytics Charts
    security:
      - Bearer: []
    """

    event = get_object_or_404(
        Event,
        id=event_id,
        description="Event not found"
    )

    total = Registration.objects(event=event).count()
    checked_in = Registration.objects(
        event=event,
        checked_in=True
    ).count()

    absent = total - checked_in

    return jsonify({
        "labels": ["Checked In", "Absent"],
        "datasets": [
            {
                "label": "Attendance",
                "data": [checked_in, absent]
            }
        ]
    }), 200


# ═════════════════════════════════════════════════════════════
# CHECK-IN SYSTEM
# ═════════════════════════════════════════════════════════════

@analytics_bp.route("/checkin/scan", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def checkin_scan():
    """
    Scan QR and check in attendee
    ---
    tags:
      - QR Check-In
    security:
      - Bearer: []
    responses:
      200:
        description: Check-in completed
    """

    data = request.get_json()

    qr_token = data.get("qr_token", "").strip()

    if not qr_token:
        return jsonify({
            "error": "qr_token is required"
        }), 400

    registration = Registration.objects(
        qr_token=qr_token
    ).first()

    if not registration:
        return jsonify({
            "error": "Invalid QR token"
        }), 404

    if registration.checked_in:
        return jsonify({
            "message": "Already checked in",
            "checked_in_at": (
                registration.checked_in_at.isoformat()
                if registration.checked_in_at
                else None
            )
        }), 200

    registration.checked_in = True
    registration.checked_in_at = datetime.now(timezone.utc)
    registration.save()

    return jsonify({
        "message": "Checked in successfully",
        "registration": registration.to_dict()
    }), 200


@analytics_bp.route("/checkin/history", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def checkin_history():
    """
    Get event check-in history
    ---
    tags:
      - QR Check-In
    security:
      - Bearer: []
    """

    event_id = request.args.get("event_id")

    if not event_id:
        return jsonify({
            "error": "event_id is required"
        }), 400

    event = get_object_or_404(
        Event,
        id=event_id,
        description="Event not found"
    )

    registrations = Registration.objects(event=event)

    return jsonify({
        "event": event.title,
        "total": registrations.count(),
        "registrations": [
            r.to_dict() for r in registrations
        ]
    }), 200


# ═════════════════════════════════════════════════════════════
# QR GENERATION
# ═════════════════════════════════════════════════════════════

def _get_qr_image_bytes(reg_id):

    if reg_id in _qr_cache:
        return _qr_cache[reg_id]

    reg = Registration.objects(id=reg_id).first()

    if not reg:
        return None

    if not reg.qr_token:
        reg.generate_qr_token()
        reg.save()

    img_bytes = generate_qr_image(
        str(reg.id),
        reg.qr_token
    )

    if img_bytes:
        _qr_cache[reg_id] = img_bytes

    return img_bytes


@analytics_bp.route("/qr/<reg_id>", methods=["GET"])
@jwt_required()
def get_qr_code(reg_id):
    """
    Get QR PNG image
    ---
    tags:
      - QR Check-In
    security:
      - Bearer: []
    """

    registration = get_object_or_404(
        Registration,
        id=reg_id,
        description="Registration not found"
    )

    user = get_current_user()

    if (
        user.role not in ("admin", "organizer")
        and str(user.id) != str(registration.user.id)
    ):
        return jsonify({
            "error": "Access denied"
        }), 403

    img_bytes = _get_qr_image_bytes(reg_id)

    if not img_bytes:
        return jsonify({
            "error": "QR generation unavailable"
        }), 503

    return Response(
        img_bytes,
        mimetype="image/png",
        headers={
            "Content-Disposition":
                f"inline; filename=qr_{reg_id}.png"
        }
    )


@analytics_bp.route("/qr/<reg_id>/token", methods=["GET"])
@jwt_required()
def get_qr_token(reg_id):
    """
    Get QR token JSON
    ---
    tags:
      - QR Check-In
    security:
      - Bearer: []
    """

    registration = get_object_or_404(
        Registration,
        id=reg_id,
        description="Registration not found"
    )

    user = get_current_user()

    if (
        user.role not in ("admin", "organizer")
        and str(user.id) != str(registration.user.id)
    ):
        return jsonify({
            "error": "Access denied"
        }), 403

    if not registration.qr_token:
        registration.generate_qr_token()
        registration.save()

    return jsonify({
        "registration_id": str(registration.id),
        "event_id": str(registration.event.id),
        "event_title": registration.event.title,
        "user_id": str(registration.user.id),
        "qr_token": registration.qr_token,
        "checked_in": registration.checked_in,
        "checked_in_at": (
            registration.checked_in_at.isoformat()
            if registration.checked_in_at
            else None
        )
    }), 200


# ═════════════════════════════════════════════════════════════
# REPORTS & INSIGHTS
# ═════════════════════════════════════════════════════════════

@analytics_bp.route("/reports/summary", methods=["GET"])
@jwt_required()
@role_required("admin")
def reports_summary():
    """
    Get platform summary report
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    """

    return jsonify({
        "total_users": User.objects.count(),
        "total_events": Event.objects.count(),
        "total_registrations": Registration.objects.count(),
        "total_feedbacks": Feedback.objects.count(),
        "total_questions": Question.objects.count(),
    }), 200


@analytics_bp.route("/reports/event/<event_id>", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def event_report(event_id):
    """
    Get detailed event report
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    """

    event = get_object_or_404(
        Event,
        id=event_id,
        description="Event not found"
    )

    registrations = Registration.objects(event=event)
    feedbacks = Feedback.objects(event=event)

    return jsonify({
        "event": event.to_dict(),
        "registrations_count": registrations.count(),
        "checked_in_count": registrations.filter(
            checked_in=True
        ).count(),
        "feedback_count": feedbacks.count(),
        "questions_count": Question.objects(
            event=event
        ).count(),
    }), 200