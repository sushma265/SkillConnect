from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Announcement
from app.utils import role_required

announcements_bp = Blueprint("announcements", __name__)


# ── POST /announcements  (conductor / admin) ──────────────────────────────
@announcements_bp.route("", methods=["POST"])
@jwt_required()
@role_required("conductor", "admin")
def create_announcement():
    data = request.get_json()
    if not data.get("title") or not data.get("content"):
        return jsonify({"error": "'title' and 'content' are required"}), 400

    user_id = get_jwt_identity()
    ann = Announcement(
        title=data["title"],
        content=data["content"],
        created_by=int(user_id),
    )
    db.session.add(ann)
    db.session.commit()
    return jsonify({"message": "Announcement created", "announcement": ann.to_dict()}), 201


# ── GET /announcements  (public) ──────────────────────────────────────────
@announcements_bp.route("", methods=["GET"])
def get_announcements():
    announcements = (
        Announcement.query
        .order_by(Announcement.created_at.desc())
        .all()
    )
    return jsonify({"announcements": [a.to_dict() for a in announcements]}), 200
