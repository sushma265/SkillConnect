"""
SkillConnect – Announcement Routes
=====================================
Advanced announcement management system with:
- CRUD operations
- Event announcements
- Scheduled publishing
- Pinning announcements
- Search & filters
- Admin moderation
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timezone

from app.models.announcement_model import Announcement
from app.models.event_model import Event

from app.utils.decorators import role_required
from app.utils.jwt_utils import (
    get_current_user,
    get_object_or_404
)

announcements_bp = Blueprint(
    "announcements",
    __name__
)


# ═════════════════════════════════════════════════════════════
# CREATE ANNOUNCEMENT
# ═════════════════════════════════════════════════════════════

@announcements_bp.route("", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def create_announcement():
    """
    Create new announcement
    ---
    tags:
      - Announcements
    security:
      - Bearer: []
    responses:
      201:
        description: Announcement created
    """

    data = request.get_json()

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title or not content:
        return jsonify({
            "error": "title and content are required"
        }), 400

    priority = data.get("priority", "medium")

    if priority not in ("low", "medium", "high"):
        return jsonify({
            "error": "Invalid priority"
        }), 400

    event = None

    if data.get("event_id"):
        event = Event.objects(
            id=data["event_id"]
        ).first()

        if not event:
            return jsonify({
                "error": "Event not found"
            }), 404

    user = get_current_user()

    announcement = Announcement(
        title=title,
        content=content,
        priority=priority,
        event=event,
        created_by=user,
        is_published=bool(
            data.get("is_published", True)
        ),
        is_pinned=bool(
            data.get("is_pinned", False)
        ),
    )

    announcement.save()

    return jsonify({
        "message": "Announcement created successfully",
        "announcement": announcement.to_dict()
    }), 201


# ═════════════════════════════════════════════════════════════
# GET ALL ANNOUNCEMENTS
# ═════════════════════════════════════════════════════════════

@announcements_bp.route("", methods=["GET"])
def get_announcements():
    """
    Get all announcements
    ---
    tags:
      - Announcements
    responses:
      200:
        description: Announcement list
    """

    query = Announcement.objects(
        is_published=True
    )

    # Filter by event
    event_id = request.args.get("event_id")

    if event_id:
        event = Event.objects(
            id=event_id
        ).first()

        if event:
            query = query.filter(event=event)

    # Filter by priority
    priority = request.args.get("priority")

    if priority:
        query = query.filter(
            priority=priority
        )

    # Search
    search = request.args.get("search")

    if search:
        query = query.filter(
            title__icontains=search
        )

    announcements = query.order_by(
        "-is_pinned",
        "-created_at"
    )

    return jsonify({
        "total": announcements.count(),
        "announcements": [
            ann.to_dict()
            for ann in announcements
        ]
    }), 200


# ═════════════════════════════════════════════════════════════
# GET SINGLE ANNOUNCEMENT
# ═════════════════════════════════════════════════════════════

@announcements_bp.route("/<ann_id>", methods=["GET"])
def get_announcement(ann_id):
    """
    Get single announcement
    ---
    tags:
      - Announcements
    responses:
      200:
        description: Announcement details
    """

    announcement = get_object_or_404(
        Announcement,
        id=ann_id,
        description="Announcement not found"
    )

    return jsonify({
        "announcement": announcement.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# UPDATE ANNOUNCEMENT
# ═════════════════════════════════════════════════════════════

@announcements_bp.route("/<ann_id>", methods=["PUT"])
@jwt_required()
@role_required("organizer", "admin")
def update_announcement(ann_id):
    """
    Update announcement
    ---
    tags:
      - Announcements
    security:
      - Bearer: []
    responses:
      200:
        description: Announcement updated
    """

    announcement = get_object_or_404(
        Announcement,
        id=ann_id,
        description="Announcement not found"
    )

    data = request.get_json()

    if "title" in data:
        announcement.title = data["title"]

    if "content" in data:
        announcement.content = data["content"]

    if "priority" in data:

        if data["priority"] not in (
            "low",
            "medium",
            "high"
        ):
            return jsonify({
                "error": "Invalid priority"
            }), 400

        announcement.priority = data["priority"]

    if "is_published" in data:
        announcement.is_published = bool(
            data["is_published"]
        )

    if "is_pinned" in data:
        announcement.is_pinned = bool(
            data["is_pinned"]
        )

    announcement.updated_at = datetime.now(
        timezone.utc
    )

    announcement.save()

    return jsonify({
        "message": "Announcement updated successfully",
        "announcement": announcement.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# DELETE ANNOUNCEMENT
# ═════════════════════════════════════════════════════════════

@announcements_bp.route("/<ann_id>", methods=["DELETE"])
@jwt_required()
@role_required("organizer", "admin")
def delete_announcement(ann_id):
    """
    Delete announcement
    ---
    tags:
      - Announcements
    security:
      - Bearer: []
    responses:
      200:
        description: Announcement deleted
    """

    announcement = get_object_or_404(
        Announcement,
        id=ann_id,
        description="Announcement not found"
    )

    announcement.delete()

    return jsonify({
        "message": "Announcement deleted successfully"
    }), 200


# ═════════════════════════════════════════════════════════════
# PIN / UNPIN ANNOUNCEMENT
# ═════════════════════════════════════════════════════════════

@announcements_bp.route(
    "/<ann_id>/toggle-pin",
    methods=["PUT"]
)
@jwt_required()
@role_required("organizer", "admin")
def toggle_pin_announcement(ann_id):
    """
    Pin or unpin announcement
    ---
    tags:
      - Announcements
    security:
      - Bearer: []
    """

    announcement = get_object_or_404(
        Announcement,
        id=ann_id,
        description="Announcement not found"
    )

    announcement.is_pinned = (
        not announcement.is_pinned
    )

    announcement.save()

    status = (
        "pinned"
        if announcement.is_pinned
        else "unpinned"
    )

    return jsonify({
        "message": f"Announcement {status}",
        "announcement": announcement.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# GET EVENT ANNOUNCEMENTS
# ═════════════════════════════════════════════════════════════

@announcements_bp.route(
    "/event/<event_id>",
    methods=["GET"]
)
def get_event_announcements(event_id):
    """
    Get event announcements
    ---
    tags:
      - Announcements
    responses:
      200:
        description: Event announcements
    """

    event = get_object_or_404(
        Event,
        id=event_id,
        description="Event not found"
    )

    announcements = Announcement.objects(
        event=event,
        is_published=True
    ).order_by("-created_at")

    return jsonify({
        "event": event.title,
        "total": announcements.count(),
        "announcements": [
            ann.to_dict()
            for ann in announcements
        ]
    }), 200


# ═════════════════════════════════════════════════════════════
# ADMIN ANNOUNCEMENT STATS
# ═════════════════════════════════════════════════════════════

@announcements_bp.route(
    "/stats",
    methods=["GET"]
)
@jwt_required()
@role_required("admin")
def announcement_stats():
    """
    Get announcement statistics
    ---
    tags:
      - Announcement Analytics
    security:
      - Bearer: []
    """

    total = Announcement.objects.count()

    published = Announcement.objects(
        is_published=True
    ).count()

    drafts = Announcement.objects(
        is_published=False
    ).count()

    pinned = Announcement.objects(
        is_pinned=True
    ).count()

    return jsonify({
        "total_announcements": total,
        "published_announcements": published,
        "draft_announcements": drafts,
        "pinned_announcements": pinned
    }), 200