"""
SkillConnect – Analytics Routes
==================================
Provides dashboard analytics data with Chart.js-compatible output.
Includes check-in (QR) endpoints as part of the analytics scope.
"""

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, decode_token
from datetime import datetime, timezone
import io

from app.models.registration_model import Registration
from app.models.event_model import Event
from app.models.user_model import User
from app.utils.decorators import role_required
from app.utils.jwt_utils import get_current_user, get_object_or_404
from app.utils.analytics_utils import (
    get_platform_analytics,
    get_event_analytics,
    get_participation_data,
)
from app.utils.qr_utils import generate_qr_image

analytics_bp = Blueprint("analytics", __name__)

# ── In-memory QR image cache (reg_id → PNG bytes) ──────────────────────
_qr_cache: dict = {}

try:
    import qrcode as _qr_lib
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False


# ═══════════ ANALYTICS ENDPOINTS ═══════════════════════════════════════

# ── GET /analytics/dashboard ────────────────────────────────────────────
@analytics_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def dashboard():
    """
    Get platform-wide analytics for the dashboard.
    ---
    tags: [Analytics]
    security: [{Bearer: []}]
    responses:
      200: {description: Platform analytics}
    """
    return jsonify(get_platform_analytics()), 200


# ── GET /analytics/events/<event_id> ────────────────────────────────────
@analytics_bp.route("/events/<event_id>", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def event_analytics_route(event_id):
    """
    Get analytics for a specific event.
    ---
    tags: [Analytics]
    security: [{Bearer: []}]
    """
    event = get_object_or_404(
        Event, id=event_id, description="Event not found"
    )
    return jsonify(get_event_analytics(event)), 200


# ── GET /analytics/participation ────────────────────────────────────────
@analytics_bp.route("/participation", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def participation():
    """
    Get participation/fill-rate data across all events.
    ---
    tags: [Analytics]
    security: [{Bearer: []}]
    """
    return jsonify({"events": get_participation_data()}), 200


# ═══════════ CHECK-IN (QR) ENDPOINTS ═══════════════════════════════════

# ── POST /analytics/checkin/scan (or POST /checkin/scan via admin) ──────
@analytics_bp.route("/checkin/scan", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def checkin_scan():
    """
    Scan a QR code to check in an attendee.
    ---
    tags: [Check-In]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [qr_token]
          properties:
            qr_token: {type: string}
    responses:
      200: {description: Check-in result}
    """
    data = request.get_json()
    token = data.get("qr_token", "").strip()

    if not token:
        return jsonify({"error": "qr_token is required"}), 400

    reg = Registration.objects(qr_token=token).first()
    if not reg:
        return jsonify({"error": "Invalid QR token"}), 404

    if reg.status != "confirmed":
        return jsonify({
            "error": f"Registration not confirmed (status: {reg.status})"
        }), 400

    if reg.checked_in:
        return jsonify({
            "message": "Already checked in",
            "checked_in_at": reg.checked_in_at.isoformat(),
            "attendee": reg.user.to_dict(),
        }), 200

    reg.checked_in = True
    reg.checked_in_at = datetime.now(timezone.utc)
    reg.save()

    return jsonify({
        "message": "Checked in successfully",
        "registration": reg.to_dict(),
        "attendee": reg.user.to_dict(),
    }), 200


# ── GET /analytics/checkin/history ──────────────────────────────────────
@analytics_bp.route("/checkin/history", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def checkin_history():
    """
    Get check-in history for an event.
    ---
    tags: [Check-In]
    security: [{Bearer: []}]
    parameters:
      - in: query
        name: event_id
        type: string
        required: true
    responses:
      200: {description: Check-in records}
    """
    event_id = request.args.get("event_id")
    if not event_id:
        return jsonify({
            "error": "event_id query param is required"
        }), 400

    event = get_object_or_404(
        Event, id=event_id, description="Event not found"
    )

    qs = Registration.objects(event=event)
    checked_in_filter = request.args.get("checked_in")
    if checked_in_filter == "true":
        qs = qs.filter(checked_in=True)
    elif checked_in_filter == "false":
        qs = qs.filter(checked_in=False)

    registrations = list(qs)
    total = len(registrations)
    checked_in_count = sum(1 for r in registrations if r.checked_in)

    return jsonify({
        "event_id": str(event.id),
        "event_title": event.title,
        "total_registered": total,
        "checked_in_count": checked_in_count,
        "attendance_rate": (
            round(checked_in_count / total * 100, 1) if total > 0 else 0
        ),
        "registrations": [r.to_dict() for r in registrations],
    }), 200


def _get_qr_image_bytes(reg_id: str) -> bytes | None:
    """Return cached QR PNG bytes, generating if needed."""
    if reg_id in _qr_cache:
        return _qr_cache[reg_id]
    reg = Registration.objects(id=reg_id).first()
    if not reg:
        return None
    if not reg.qr_token:
        reg.generate_qr_token()
        reg.save()
    img_bytes = generate_qr_image(str(reg.id), reg.qr_token)
    if img_bytes:
        _qr_cache[reg_id] = img_bytes
    return img_bytes


# ── GET /analytics/qr/<reg_id> ─────────────────────────────────────────
@analytics_bp.route("/qr/<reg_id>", methods=["GET"])
@jwt_required()
def get_qr_code(reg_id):
    """
    Get a QR code image (PNG) for a registration.
    ---
    tags: [Check-In]
    security: [{Bearer: []}]
    """
    reg = get_object_or_404(
        Registration, id=reg_id,
        description="Registration not found",
    )
    user = get_current_user()

    if (
        user.role not in ("admin", "organizer")
        and str(reg.user.id) != str(user.id)
    ):
        return jsonify({"error": "Access denied"}), 403

    img_bytes = _get_qr_image_bytes(reg_id)
    if not img_bytes:
        return jsonify({
            "qr_token": reg.qr_token,
            "registration_id": str(reg.id),
        }), 200

    return Response(
        img_bytes,
        mimetype="image/png",
        headers={
            "Cache-Control": "private, max-age=3600",
            "Content-Disposition": f"inline; filename=qr_{reg_id}.png",
        },
    )


# ── GET /analytics/qr/<reg_id>/blob  (token in query param for JS fetch)
@analytics_bp.route("/qr/<reg_id>/blob", methods=["GET"])
def get_qr_blob(reg_id):
    """
    Get a QR code PNG image. Accepts JWT via ?token= query param so the
    browser fetch() API can load it and convert it to an object URL.
    ---
    tags: [Check-In]
    """
    raw_token = request.args.get("token", "")
    if not raw_token:
        return jsonify({"error": "token required"}), 401

    try:
        from flask_jwt_extended import decode_token as _decode
        decoded = _decode(raw_token)
        identity = decoded.get("sub")
        user = User.objects(id=identity).first()
        if not user:
            raise ValueError("User not found")
    except Exception:
        return jsonify({"error": "Invalid token"}), 401

    reg = get_object_or_404(
        Registration, id=reg_id,
        description="Registration not found",
    )

    if (
        user.role not in ("admin", "organizer")
        and str(reg.user.id) != str(user.id)
    ):
        return jsonify({"error": "Access denied"}), 403

    img_bytes = _get_qr_image_bytes(reg_id)
    if not img_bytes:
        return jsonify({"error": "QR generation unavailable"}), 503

    return Response(
        img_bytes,
        mimetype="image/png",
        headers={
            "Cache-Control": "private, max-age=3600",
            "Content-Disposition": f"inline; filename=qr_{reg_id}.png",
        },
    )


# ── GET /analytics/qr/<reg_id>/token ───────────────────────────────────
@analytics_bp.route("/qr/<reg_id>/token", methods=["GET"])
@jwt_required()
def get_qr_token(reg_id):
    """
    Get the QR token data as JSON (for mobile apps).
    ---
    tags: [Check-In]
    security: [{Bearer: []}]
    """
    reg = get_object_or_404(
        Registration, id=reg_id,
        description="Registration not found",
    )
    user = get_current_user()

    if (
        user.role not in ("admin", "organizer")
        and str(reg.user.id) != str(user.id)
    ):
        return jsonify({"error": "Access denied"}), 403

    if not reg.qr_token:
        reg.generate_qr_token()
        reg.save()

    return jsonify({
        "registration_id": str(reg.id),
        "user_id": str(reg.user.id),
        "event_id": str(reg.event.id),
        "event_title": reg.event.title,
        "status": reg.status,
        "qr_token": reg.qr_token,
        "checked_in": reg.checked_in,
        "checked_in_at": (
            reg.checked_in_at.isoformat()
            if reg.checked_in_at
            else None
        ),
    }), 200
