"""
SkillConnect – JWT Utilities
==============================
Helper functions for JWT-protected operations: retrieving the current
user and fetching MongoEngine documents with 404 handling.
"""

from flask import abort
from flask_jwt_extended import get_jwt_identity
from mongoengine.errors import DoesNotExist, ValidationError


def get_current_user():
    """
    Return the User document for the currently-authenticated JWT identity.

    Returns:
        User instance or None if not found.
    """
    from app.models.user_model import User

    user_id = get_jwt_identity()
    try:
        return User.objects.get(id=user_id)
    except (DoesNotExist, ValidationError, Exception):
        return None


def get_object_or_404(model_class, description=None, **kwargs):
    """
    Fetch a MongoEngine document or raise a 404 error.

    Args:
        model_class: The MongoEngine Document subclass to query.
        description: Optional error description for the 404 response.
        **kwargs: Query filters passed to `objects.get(...)`.

    Returns:
        The matched document instance.

    Raises:
        404 HTTPException if not found.
    """
    try:
        return model_class.objects.get(**kwargs)
    except (DoesNotExist, ValidationError, Exception):
        abort(
            404,
            description=(
                description or f"{model_class.__name__} not found"
            ),
        )
