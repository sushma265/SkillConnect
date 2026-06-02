"""
SkillConnect – QR Code Utilities
===================================
Generates and validates QR codes for event check-in.
"""

import io
from typing import Optional, Tuple

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_H

    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False


def generate_qr_image(
    registration_id: str,
    qr_token: str,
    box_size: int = 10,
    border: int = 4,
) -> Optional[bytes]:
    """
    Generate a QR code PNG image from a registration token.

    The encoded data follows the format:
        SKILLCONNECT:REG:<registration_id>:TOKEN:<qr_token>

    Args:
        registration_id: The MongoDB ObjectId of the registration.
        qr_token: The cryptographic token for the registration.
        box_size: Pixel size of each QR module.
        border: Number of blank modules around the QR code.

    Returns:
        PNG image bytes, or None if the qrcode library is unavailable.
    """
    if not QR_AVAILABLE:
        return None

    qr_data = (
        f"SKILLCONNECT:REG:{registration_id}:TOKEN:{qr_token}"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def validate_qr_token(qr_token: str) -> Tuple[bool, Optional[dict]]:
    """
    Validate a QR token against the registrations collection.

    Args:
        qr_token: The scanned QR token string.

    Returns:
        Tuple of (is_valid, registration_dict or error_info).
    """
    from app.models.registration_model import Registration

    if not qr_token or not qr_token.strip():
        return False, {"error": "Empty QR token"}

    reg = Registration.objects(qr_token=qr_token.strip()).first()

    if not reg:
        return False, {"error": "Invalid QR token"}

    if reg.status != "confirmed":
        return False, {
            "error": f"Registration not confirmed (status: {reg.status})",
            "registration_id": str(reg.id),
        }

    return True, {
        "registration_id": str(reg.id),
        "user_id": str(reg.user.id) if reg.user else None,
        "event_id": str(reg.event.id) if reg.event else None,
        "checked_in": reg.checked_in,
    }


def parse_qr_data(qr_string: str) -> Optional[dict]:
    """
    Parse a scanned QR code string into its components.

    Expected format:
        SKILLCONNECT:REG:<reg_id>:TOKEN:<token>

    Args:
        qr_string: Raw scanned QR code content.

    Returns:
        dict with 'registration_id' and 'token', or None.
    """
    if not qr_string or not qr_string.startswith("SKILLCONNECT:REG:"):
        return None

    parts = qr_string.split(":")
    if len(parts) < 5 or parts[3] != "TOKEN":
        return None

    return {
        "registration_id": parts[2],
        "token": parts[4],
    }
