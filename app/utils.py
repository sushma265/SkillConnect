from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request
from app.models import User


def role_required(*roles):
    """Decorator – allows access only to users with one of the specified roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role", "user")
            if user_role not in roles:
                return jsonify({
                    "error": f"Access denied. Required role(s): {list(roles)}"
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user():
    """Return the User object for the current JWT identity."""
    user_id = get_jwt_identity()
    return User.query.get(user_id)
