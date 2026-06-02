"""
SkillConnect – Session Material Model
========================================
Stores downloadable / linkable materials attached to sessions
(PDFs, slides, videos, links, etc.).
"""

from mongoengine import (
    Document, StringField, DateTimeField, ReferenceField
)
from datetime import datetime, timezone


def now_utc():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class SessionMaterial(Document):
    """
    A material resource attached to a session.

    Fields:
        session       – Parent Session reference (required).
        title         – Material title (required).
        material_type – link | pdf | slide | video | image | other.
        url           – URL to the resource (required).
        description   – Optional description.
        created_by    – Organiser who uploaded the material.
        created_at    – Creation timestamp.
    """

    meta = {
        "collection": "materials",
        "ordering": ["created_at"],
    }

    session = ReferenceField("Session", required=True)
    title = StringField(required=True, max_length=200)
    material_type = StringField(
        default="link",
        choices=["link", "pdf", "slide", "video", "image", "other"],
    )
    url = StringField(required=True)
    description = StringField()
    created_by = ReferenceField("User", required=True)
    created_at = DateTimeField(default=now_utc)

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary."""
        return {
            "id": str(self.id),
            "session_id": (
                str(self.session.id) if self.session else None
            ),
            "session_title": (
                self.session.title if self.session else None
            ),
            "title": self.title,
            "material_type": self.material_type,
            "url": self.url,
            "description": self.description,
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
        return f"<SessionMaterial {self.title[:40]}>"
