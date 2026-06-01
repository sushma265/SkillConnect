from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Announcement
from app.utils import role_required

announcements_bp = Blueprint("announcements", __name__)


@announcements_bp.route("", methods=["POST"])
@jwt_required()
@role_required("conductor", "admin")
def create_announcement():
    """
    Create Announcement API
    ---
    tags:
      - Announcements

    security:
      - Bearer: []

    consumes:
      - application/json

    parameters:
      - in: body
        name: body
        required: true

        schema:
          type: object

          required:
            - title
            - content

          properties:
            title:
              type: string
              example: New Workshop Launch

            content:
              type: string
              example: Python workshop registrations are now open.

    responses:
      201:
        description: Announcement created successfully

      400:
        description: Missing title or content

      401:
        description: Unauthorized

      403:
        description: Access denied
    """

    data = request.get_json()

    if not data.get("title") or not data.get("content"):
        return jsonify({
            "error": "title and content are required"
        }), 400

    user_id = get_jwt_identity()

    ann = Announcement(
        title=data["title"],
        content=data["content"],
        created_by=int(user_id),
    )

    db.session.add(ann)
    db.session.commit()

    return jsonify({
        "message": "Announcement created",
        "announcement": ann.to_dict()
    }), 201


@announcements_bp.route("", methods=["GET"])
def get_announcements():
    """
    Get Announcements API
    ---
    tags:
      - Announcements

    responses:
      200:
        description: List of announcements returned
    """

    announcements = (
        Announcement.query
        .order_by(Announcement.created_at.desc())
        .all()
    )

    return jsonify({
        "announcements": [
            a.to_dict() for a in announcements
        ]
    }), 200