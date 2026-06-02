"""
SkillConnect – Decorators
===========================
Custom Flask decorators for role-based access control.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def role_required(*roles):
    """
    Decorator that restricts endpoint access to users whose JWT 'role'
    claim matches one of the specified roles.

    Usage:
        @role_required("organizer", "admin")
        def create_event():
            ...

    Args:
        *roles: One or more allowed role strings
                (e.g. "attendee", "organizer", "admin").

    Returns:
        Wrapped function that returns 403 if the user's role is not in
        the allowed set.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Ensure a valid JWT is present
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role", "attendee")

            if user_role not in roles:
                return jsonify({
                    "error": (
                        f"Access denied. "
                        f"Required role(s): {list(roles)}"
                    )
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
