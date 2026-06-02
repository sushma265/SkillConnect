"""
SkillConnect – Announcement Model
====================================
Stores platform-wide or event-specific announcements.
"""

from mongoengine import (
    Document, StringField, BooleanField, DateTimeField, ReferenceField
)
from datetime import datetime, timezone


def now_utc():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class Announcement(Document):
    """
    A platform or event announcement posted by an organiser.

    Fields:
        title        – Announcement title (required).
        content      – Full announcement body (required).
        event        – Optional event scope.
        priority     – low | medium | high.
        is_published – Visibility toggle.
        created_by   – Organiser who posted the announcement.
        created_at   – Creation timestamp.
    """

    meta = {
        "collection": "announcements",
        "ordering": ["-created_at"],
    }

    title = StringField(required=True, max_length=200)
    content = StringField(required=True)
    event = ReferenceField("Event", null=True)
    priority = StringField(
        default="medium",
        choices=["low", "medium", "high"],
    )
    is_published = BooleanField(default=True)
    created_by = ReferenceField("User", required=True)
    created_at = DateTimeField(default=now_utc)

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "content": self.content,
            "event_id": (
                str(self.event.id) if self.event else None
            ),
            "priority": self.priority,
            "is_published": self.is_published,
            "created_by": (
                str(self.created_by.id) if self.created_by else None
            ),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }

    def __repr__(self) -> str:
        return f"<Announcement {self.title[:40]}>"
