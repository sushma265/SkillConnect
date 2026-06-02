"""
SkillConnect – Feedback Model
================================
Stores user feedback/ratings for events and sessions.
"""

from mongoengine import (
    Document, StringField, IntField, DateTimeField, ReferenceField
)
from datetime import datetime, timezone


def now_utc():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class Feedback(Document):
    """
    User-submitted feedback for an event or session.

    Fields:
        user          – The user providing feedback (required).
        event         – Event being reviewed (nullable).
        session       – Session being reviewed (nullable).
        rating        – Integer rating 1–5 (required).
        comment       – Free-text comment.
        feedback_type – 'event' or 'session'.
        created_at    – Submission timestamp.
    """

    meta = {
        "collection": "feedback",
        "ordering": ["-created_at"],
    }

    user = ReferenceField("User", required=True)
    event = ReferenceField("Event", null=True)
    session = ReferenceField("Session", null=True)
    rating = IntField(required=True, min_value=1, max_value=5)
    comment = StringField()
    feedback_type = StringField(choices=["event", "session"])
    created_at = DateTimeField(default=now_utc)

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user.id) if self.user else None,
            "user_name": self.user.name if self.user else None,
            "event_id": (
                str(self.event.id) if self.event else None
            ),
            "session_id": (
                str(self.session.id) if self.session else None
            ),
            "rating": self.rating,
            "comment": self.comment,
            "feedback_type": self.feedback_type,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }

    def __repr__(self) -> str:
        return f"<Feedback rating={self.rating} by={self.user.id}>"
