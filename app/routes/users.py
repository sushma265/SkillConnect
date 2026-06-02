"""
SkillConnect – User Profile Routes
=====================================
Handles user profile viewing, updating, and search.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.user_model import User
from app.utils.jwt_utils import get_current_user, get_object_or_404
from app.utils.decorators import role_required

users_bp = Blueprint("users", __name__)


# ── GET /users/profile ──────────────────────────────────────────────────
@users_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """
    Get the current user's full profile.
    ---
    tags: [Users]
    security: [{Bearer: []}]
    responses:
      200: {description: User profile}
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


# ── PUT /users/profile ──────────────────────────────────────────────────
@users_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """
    Update the current user's profile.
    ---
    tags: [Users]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            name:         {type: string}
            bio:          {type: string}
            company:      {type: string}
            job_title:    {type: string}
            linkedin_url: {type: string}
            avatar_url:   {type: string}
    responses:
      200: {description: Profile updated}
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    updatable_fields = [
        "name", "bio", "company", "job_title",
        "linkedin_url", "avatar_url",
    ]

    for field in updatable_fields:
        if field in data:
            setattr(user, field, data[field])

    user.save()
    return jsonify({
        "message": "Profile updated",
        "user": user.to_dict(),
    }), 200


# ── PUT /users/change-password ──────────────────────────────────────────
@users_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    """
    Change the current user's password.
    ---
    tags: [Users]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [current_password, new_password]
          properties:
            current_password: {type: string}
            new_password:     {type: string}
    responses:
      200: {description: Password changed}
      400: {description: Current password incorrect}
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    current = data.get("current_password")
    new_pw = data.get("new_password")

    if not current or not new_pw:
        return jsonify({
            "error": "current_password and new_password are required"
        }), 400

    if not user.check_password(current):
        return jsonify({
            "error": "Current password is incorrect"
        }), 400

    if len(new_pw) < 6:
        return jsonify({
            "error": "New password must be at least 6 characters"
        }), 400

    user.set_password(new_pw)
    user.save()
    return jsonify({"message": "Password changed successfully"}), 200


# ── GET /users/<user_id> ────────────────────────────────────────────────
@users_bp.route("/<user_id>", methods=["GET"])
@jwt_required()
def get_user_by_id(user_id):
    """
    Get a user's public profile by ID.
    ---
    tags: [Users]
    security: [{Bearer: []}]
    responses:
      200: {description: User profile}
    """
    user = get_object_or_404(
        User, id=user_id, description="User not found"
    )
    # Return limited public profile
    return jsonify({
        "user": {
            "id": str(user.id),
            "name": user.name,
            "role": user.role,
            "bio": user.bio,
            "company": user.company,
            "job_title": user.job_title,
            "linkedin_url": user.linkedin_url,
            "avatar_url": user.avatar_url,
        }
    }), 200


# ── GET /users/search ──────────────────────────────────────────────────
@users_bp.route("/search", methods=["GET"])
@jwt_required()
def search_users():
    """
    Search users by name or email.
    ---
    tags: [Users]
    security: [{Bearer: []}]
    parameters:
      - in: query
        name: q
        type: string
        required: true
    responses:
      200: {description: Matching users}
    """
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        return jsonify({
            "error": "Query must be at least 2 characters"
        }), 400

    # Search by name or email (case-insensitive regex)
    users = User.objects(
        __raw__={
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}},
            ],
            "is_active": True,
        }
    ).limit(20)

    return jsonify({
        "users": [
            {
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "company": u.company,
                "job_title": u.job_title,
                "avatar_url": u.avatar_url,
            }
            for u in users
        ]
    }), 200


# ── GET /users/attendees ───────────────────────────────────────────────
@users_bp.route("/attendees", methods=["GET"])
@jwt_required()
@role_required("organizer", "admin")
def list_attendees():
    """
    List all attendee users (organizer/admin only).
    ---
    tags: [Users]
    security: [{Bearer: []}]
    responses:
      200: {description: List of attendees}
    """
    attendees = User.objects(
        role="attendee", is_active=True
    ).order_by("name")
    return jsonify({
        "total": attendees.count(),
        "attendees": [u.to_dict() for u in attendees],
    }), 200
