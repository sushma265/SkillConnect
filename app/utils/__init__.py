"""
SkillConnect – Utilities Package
==================================
Re-exports commonly used utilities for convenient imports.

Usage:
    from app.utils import role_required, get_current_user, ...
"""

from app.utils.decorators import role_required
from app.utils.jwt_utils import get_current_user, get_object_or_404
from app.utils.qr_utils import generate_qr_image, validate_qr_token
from app.utils.analytics_utils import (
    get_platform_analytics,
    get_event_analytics,
    get_participation_data,
)

__all__ = [
    "role_required",
    "get_current_user",
    "get_object_or_404",
    "generate_qr_image",
    "validate_qr_token",
    "get_platform_analytics",
    "get_event_analytics",
    "get_participation_data",
]
