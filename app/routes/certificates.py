"""
SkillConnect – Certificates Route
====================================
Endpoints:
  POST /certificates/issue/<event_id>  – Organizer issues certs to all confirmed attendees
  GET  /certificates/my                – Attendee fetches their own certificates
  GET  /certificates/<cert_uuid>       – Public endpoint to verify a certificate
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timezone

from app.models.certificate_model import Certificate
from app.models.event_model import Event
from app.models.registration_model import Registration
from app.models.user_model import User
from app.utils.decorators import role_required
from app.utils.jwt_utils import get_current_user, get_object_or_404
from mongoengine.errors import NotUniqueError

certificates_bp = Blueprint("certificates", __name__)


# ── POST /certificates/issue/<event_id> ─────────────────────────────────
@certificates_bp.route("/issue/<event_id>", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def issue_certificates(event_id):
    """
    Issue certificates to all confirmed (and optionally checked-in)
    attendees of an event. Skips attendees who already have a certificate.

    Only the event creator or an admin may call this endpoint.

    Returns:
        {
            "message": "Certificates issued",
            "issued":   <count of new certs>,
            "skipped":  <count already had cert>
        }
    """
    issuer = get_current_user()
    ev = get_object_or_404(Event, id=event_id, description="Event not found")

    # Only the organizer who created the event (or an admin) may issue
    if issuer.role != "admin" and str(ev.created_by.id) != str(issuer.id):
        return jsonify({"error": "You can only issue certificates for your own events"}), 403

    # Fetch all confirmed registrations
    regs = Registration.objects(event=ev, status="confirmed")

    issued = 0
    skipped = 0

    # Format event date nicely
    event_date_str = ""
    if ev.event_date:
        event_date_str = ev.event_date.strftime("%-d %b %Y") if hasattr(ev.event_date, 'strftime') else str(ev.event_date)
        try:
            event_date_str = ev.event_date.strftime("%d %b %Y")
        except Exception:
            event_date_str = str(ev.event_date)[:10]

    for reg in regs:
        try:
            attendee = reg.user
            cert = Certificate(
                certificate_id=Certificate.generate_id(),
                recipient=attendee,
                event=ev,
                issued_by=issuer,
                recipient_name=attendee.name,
                event_title=ev.title,
                organizer_name=issuer.name,
                event_date=event_date_str,
            )
            cert.save()
            issued += 1
        except NotUniqueError:
            # Certificate already exists for this user+event pair
            skipped += 1
        except Exception:
            skipped += 1

    return jsonify({
        "message": f"Certificates issued to {issued} attendee(s).",
        "issued": issued,
        "skipped": skipped,
    }), 200


# ── GET /certificates/my ────────────────────────────────────────────────
@certificates_bp.route("/my", methods=["GET"])
@jwt_required()
def my_certificates():
    """
    Return all certificates earned by the currently authenticated user.
    """
    user = get_current_user()
    certs = Certificate.objects(recipient=user).order_by("-issued_at")
    return jsonify({
        "certificates": [c.to_dict() for c in certs]
    }), 200


# ── GET /certificates/<cert_uuid> ───────────────────────────────────────
@certificates_bp.route("/<cert_uuid>", methods=["GET"])
def verify_certificate(cert_uuid):
    """
    Public endpoint to verify a certificate by its UUID.
    Returns certificate data for the public verification page.
    """
    try:
        cert = Certificate.objects.get(certificate_id=cert_uuid)
    except Exception:
        return jsonify({"error": "Certificate not found or invalid"}), 404

    return jsonify({"certificate": cert.to_dict()}), 200


# ── GET /certificates/event/<event_id> ──────────────────────────────────
@certificates_bp.route("/event/<event_id>", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def event_certificates(event_id):
    """
    Organizer: list all certificates issued for a specific event.
    """
    issuer = get_current_user()
    ev = get_object_or_404(Event, id=event_id, description="Event not found")

    if issuer.role != "admin" and str(ev.created_by.id) != str(issuer.id):
        return jsonify({"error": "Access denied"}), 403

    certs = Certificate.objects(event=ev).order_by("recipient_name")
    total_regs = Registration.objects(event=ev, status="confirmed").count()

    return jsonify({
        "certificates": [c.to_dict() for c in certs],
        "total_confirmed": total_regs,
        "total_issued": certs.count(),
    }), 200
