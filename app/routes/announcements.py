"""
SkillConnect – Announcement Routes
=====================================
CRUD for platform and event announcements.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.models.announcement_model import Announcement
from app.models.event_model import Event
from app.utils.decorators import role_required
from app.utils.jwt_utils import get_current_user, get_object_or_404

announcements_bp = Blueprint("announcements", __name__)


# ── POST /announcements ────────────────────────────────────────────────
@announcements_bp.route("", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def create_announcement():
    """
    Post a new announcement.
    ---
    tags: [Announcements]
    security: [{Bearer: []}]
    """
    data = request.get_json()

    if not data.get("title") or not data.get("content"):
        return jsonify({
            "error": "title and content are required"
        }), 400

    priority = data.get("priority", "medium")
    if priority not in ("low", "medium", "high"):
        return jsonify({
            "error": "priority must be 'low', 'medium', or 'high'"
        }), 400

    user = get_current_user()

    event = None
    if data.get("event_id"):
        event = Event.objects(id=data["event_id"]).first()

    ann = Announcement(
        title=data["title"],
        content=data["content"],
        event=event,
        priority=priority,
        is_published=bool(data.get("is_published", True)),
        created_by=user,
    )
    ann.save()

    return jsonify({
        "message": "Announcement created",
        "announcement": ann.to_dict(),
    }), 201


# ── GET /announcements ─────────────────────────────────────────────────
@announcements_bp.route("", methods=["GET"])
def get_announcements():
    """
    Get all published announcements.
    ---
    tags: [Announcements]
    """
    qs = Announcement.objects(is_published=True)

    if request.args.get("event_id"):
        event = Event.objects(
            id=request.args["event_id"]
        ).first()
        if event:
            qs = qs.filter(event=event)

    if request.args.get("priority"):
        qs = qs.filter(priority=request.args["priority"])

    anns = qs.order_by("-created_at")
    return jsonify({
        "announcements": [a.to_dict() for a in anns]
    }), 200


# ── GET /announcements/<id> ────────────────────────────────────────────
@announcements_bp.route("/<ann_id>", methods=["GET"])
def get_announcement(ann_id):
    """
    Get a single announcement by ID.
    ---
    tags: [Announcements]
    """
    ann = get_object_or_404(
        Announcement, id=ann_id,
        description="Announcement not found",
    )
    return jsonify({"announcement": ann.to_dict()}), 200


# ── PUT /announcements/<id> ────────────────────────────────────────────
@announcements_bp.route("/<ann_id>", methods=["PUT"])
@jwt_required()
@role_required("organizer", "admin")
def update_announcement(ann_id):
    """
    Update an announcement.
    ---
    tags: [Announcements]
    security: [{Bearer: []}]
    """
    ann = get_object_or_404(
        Announcement, id=ann_id,
        description="Announcement not found",
    )
    data = request.get_json()

    for field in ["title", "content"]:
        if field in data:
            setattr(ann, field, data[field])

    if "priority" in data:
        if data["priority"] not in ("low", "medium", "high"):
            return jsonify({"error": "Invalid priority"}), 400
        ann.priority = data["priority"]

    if "is_published" in data:
        ann.is_published = bool(data["is_published"])

    ann.save()
    return jsonify({
        "message": "Announcement updated",
        "announcement": ann.to_dict(),
    }), 200


# ── DELETE /announcements/<id> ─────────────────────────────────────────
@announcements_bp.route("/<ann_id>", methods=["DELETE"])
@jwt_required()
@role_required("organizer", "admin")
def delete_announcement(ann_id):
    """
    Delete an announcement.
    ---
    tags: [Announcements]
    security: [{Bearer: []}]
    """
    ann = get_object_or_404(
        Announcement, id=ann_id,
        description="Announcement not found",
    )
    ann.delete()
    return jsonify({"message": "Announcement deleted"}), 200