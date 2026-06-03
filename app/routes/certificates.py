"""
SkillConnect – Certificate Routes
====================================
Advanced certificate management system with:
- Bulk certificate issuing
- Certificate verification
- Download support
- Event-wise certificates
- User certificates
- Analytics
"""

from flask import (
    Blueprint,
    jsonify,
    request,
)

from flask_jwt_extended import jwt_required

from datetime import datetime, timezone

from mongoengine.errors import NotUniqueError

from app.models.certificate_model import Certificate
from app.models.event_model import Event
from app.models.registration_model import Registration
from app.models.user_model import User

from app.utils.decorators import role_required

from app.utils.jwt_utils import (
    get_current_user,
    get_object_or_404
)

certificates_bp = Blueprint(
    "certificates",
    __name__
)


# ═════════════════════════════════════════════════════════════
# ISSUE CERTIFICATES
# ═════════════════════════════════════════════════════════════

@certificates_bp.route(
    "/issue/<event_id>",
    methods=["POST"]
)
@jwt_required()
@role_required("organizer", "admin")
def issue_certificates(event_id):
    """
    Issue certificates to attendees
    ---
    tags:
      - Certificates
    security:
      - Bearer: []
    responses:
      200:
        description: Certificates issued
    """

    issuer = get_current_user()

    event = get_object_or_404(
        Event,
        id=event_id,
        description="Event not found"
    )

    # Only event creator or admin
    if (
        issuer.role != "admin"
        and str(event.created_by.id)
        != str(issuer.id)
    ):
        return jsonify({
            "error":
                "You can only issue certificates "
                "for your own events"
        }), 403

    registrations = Registration.objects(
        event=event,
        status="confirmed"
    )

    issued = 0
    skipped = 0

    # Optional check-in validation
    require_checkin = request.args.get(
        "require_checkin",
        "false"
    ).lower() == "true"

    if require_checkin:
        registrations = registrations.filter(
            checked_in=True
        )

    event_date_str = ""

    if event.event_date:
        try:
            event_date_str = (
                event.event_date.strftime(
                    "%d %b %Y"
                )
            )
        except Exception:
            event_date_str = (
                str(event.event_date)[:10]
            )

    for registration in registrations:

        attendee = registration.user

        try:

            certificate = Certificate(
                certificate_id=
                    Certificate.generate_id(),

                recipient=attendee,

                event=event,

                issued_by=issuer,

                recipient_name=attendee.name,

                event_title=event.title,

                organizer_name=issuer.name,

                event_date=event_date_str,
            )

            certificate.save()

            issued += 1

        except NotUniqueError:

            skipped += 1

        except Exception:

            skipped += 1

    return jsonify({
        "message":
            f"Certificates issued "
            f"to {issued} attendee(s)",

        "issued": issued,

        "skipped": skipped,

        "event": event.title,
    }), 200


# ═════════════════════════════════════════════════════════════
# MY CERTIFICATES
# ═════════════════════════════════════════════════════════════

@certificates_bp.route(
    "/my",
    methods=["GET"]
)
@jwt_required()
def my_certificates():
    """
    Get current user's certificates
    ---
    tags:
      - Certificates
    security:
      - Bearer: []
    """

    user = get_current_user()

    certificates = Certificate.objects(
        recipient=user
    ).order_by("-issued_at")

    return jsonify({
        "total": certificates.count(),
        "certificates": [
            cert.to_dict()
            for cert in certificates
        ]
    }), 200


# ═════════════════════════════════════════════════════════════
# VERIFY CERTIFICATE
# ═════════════════════════════════════════════════════════════

@certificates_bp.route(
    "/verify/<certificate_id>",
    methods=["GET"]
)
def verify_certificate(certificate_id):
    """
    Verify certificate publicly
    ---
    tags:
      - Certificate Verification
    responses:
      200:
        description: Certificate verified
    """

    certificate = Certificate.objects(
        certificate_id=certificate_id
    ).first()

    if not certificate:
        return jsonify({
            "error":
                "Certificate not found or invalid"
        }), 404

    return jsonify({
        "valid": True,
        "certificate":
            certificate.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# GET EVENT CERTIFICATES
# ═════════════════════════════════════════════════════════════

@certificates_bp.route(
    "/event/<event_id>",
    methods=["GET"]
)
@jwt_required()
@role_required("organizer", "admin")
def event_certificates(event_id):
    """
    Get certificates for event
    ---
    tags:
      - Certificates
    security:
      - Bearer: []
    """

    issuer = get_current_user()

    event = get_object_or_404(
        Event,
        id=event_id,
        description="Event not found"
    )

    if (
        issuer.role != "admin"
        and str(event.created_by.id)
        != str(issuer.id)
    ):
        return jsonify({
            "error": "Access denied"
        }), 403

    certificates = Certificate.objects(
        event=event
    ).order_by("recipient_name")

    total_confirmed = Registration.objects(
        event=event,
        status="confirmed"
    ).count()

    checked_in = Registration.objects(
        event=event,
        checked_in=True
    ).count()

    return jsonify({
        "event": event.title,

        "total_confirmed":
            total_confirmed,

        "checked_in":
            checked_in,

        "total_issued":
            certificates.count(),

        "certificates": [
            cert.to_dict()
            for cert in certificates
        ]
    }), 200


# ═════════════════════════════════════════════════════════════
# GET SINGLE CERTIFICATE
# ═════════════════════════════════════════════════════════════

@certificates_bp.route(
    "/<certificate_id>",
    methods=["GET"]
)
@jwt_required()
def get_certificate(certificate_id):
    """
    Get certificate details
    ---
    tags:
      - Certificates
    security:
      - Bearer: []
    """

    certificate = Certificate.objects(
        certificate_id=certificate_id
    ).first()

    if not certificate:
        return jsonify({
            "error": "Certificate not found"
        }), 404

    user = get_current_user()

    if (
        user.role not in (
            "admin",
            "organizer"
        )
        and str(certificate.recipient.id)
        != str(user.id)
    ):
        return jsonify({
            "error": "Access denied"
        }), 403

    return jsonify({
        "certificate":
            certificate.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# DELETE CERTIFICATE
# ═════════════════════════════════════════════════════════════

@certificates_bp.route(
    "/<certificate_id>",
    methods=["DELETE"]
)
@jwt_required()
@role_required("admin")
def delete_certificate(certificate_id):
    """
    Delete certificate
    ---
    tags:
      - Certificates Admin
    security:
      - Bearer: []
    """

    certificate = Certificate.objects(
        certificate_id=certificate_id
    ).first()

    if not certificate:
        return jsonify({
            "error": "Certificate not found"
        }), 404

    certificate.delete()

    return jsonify({
        "message":
            "Certificate deleted successfully"
    }), 200


# ═════════════════════════════════════════════════════════════
# CERTIFICATE ANALYTICS
# ═════════════════════════════════════════════════════════════

@certificates_bp.route(
    "/analytics/overview",
    methods=["GET"]
)
@jwt_required()
@role_required("admin")
def certificate_analytics():
    """
    Get certificate analytics
    ---
    tags:
      - Certificate Analytics
    security:
      - Bearer: []
    """

    total_certificates = (
        Certificate.objects.count()
    )

    total_events = (
        Event.objects.count()
    )

    total_users = (
        User.objects.count()
    )

    return jsonify({
        "total_certificates":
            total_certificates,

        "total_events":
            total_events,

        "total_users":
            total_users,
    }), 200


# ═════════════════════════════════════════════════════════════
# REGENERATE CERTIFICATE
# ═════════════════════════════════════════════════════════════

@certificates_bp.route(
    "/regenerate/<certificate_id>",
    methods=["POST"]
)
@jwt_required()
@role_required("admin")
def regenerate_certificate(certificate_id):
    """
    Regenerate certificate ID
    ---
    tags:
      - Certificates Admin
    security:
      - Bearer: []
    """

    certificate = Certificate.objects(
        certificate_id=certificate_id
    ).first()

    if not certificate:
        return jsonify({
            "error": "Certificate not found"
        }), 404

    old_id = certificate.certificate_id

    certificate.certificate_id = (
        Certificate.generate_id()
    )

    certificate.updated_at = datetime.now(
        timezone.utc
    )

    certificate.save()

    return jsonify({
        "message":
            "Certificate regenerated successfully",

        "old_certificate_id":
            old_id,

        "new_certificate_id":
            certificate.certificate_id,
    }), 200