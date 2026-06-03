"""
SkillConnect – Event Model
===========================
Stores events and workshops created by organisers.
Tracks capacity, pricing, tags, and virtual meeting links.
"""

from mongoengine import (
    Document, StringField, IntField, FloatField, BooleanField,
    DateTimeField, ReferenceField, ListField
)
from datetime import datetime, timezone


def now_utc():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class Event(Document):
    """
    Represents a platform event or workshop.

    Fields:
        title        – Event title (required).
        description  – Detailed description (required).
        event_type   – 'event' or 'workshop'.
        venue        – Physical location.
        event_date   – Start date and time (required).
        end_date     – Optional scheduled end date and time.
        price        – Ticket price in INR (0 = free).
        capacity     – Maximum attendee count.
        banner_url   – Banner image URL.
        tags         – List of keyword tags.
        is_virtual   – Whether the event is online.
        meeting_link – Virtual meeting URL (Zoom, Meet, etc.).
        is_ended     – True once organizer marks the event as ended.
        ended_at     – Timestamp when the event was ended.
        created_by   – Reference to the organiser User.
        created_at   – Timestamp of creation.
        updated_at   – Timestamp of last update.
    """

    meta = {
        "collection": "events",
        "ordering": ["-event_date"],
    }

    title = StringField(required=True, max_length=200)
    description = StringField(required=True)
    event_type = StringField(
        default="event", choices=["event", "workshop"]
    )
    venue = StringField()
    event_date = DateTimeField(required=True)
    end_date = DateTimeField()
    price = FloatField(default=0.0)
    capacity = IntField(default=100)
    banner_url = StringField()
    tags = ListField(StringField())
    is_virtual = BooleanField(default=False)
    meeting_link = StringField()
    is_ended = BooleanField(default=False)
    ended_at = DateTimeField()
    created_by = ReferenceField("User", required=True)
    created_at = DateTimeField(default=now_utc)
    updated_at = DateTimeField(default=now_utc)

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary of the event."""
        # Lazy imports to avoid circular dependencies
        from app.models.registration_model import Registration
        from app.models.session_model import Session

        reg_count = Registration.objects(event=self).count()
        sess_count = Session.objects(event=self).count()

        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "venue": self.venue,
            "event_date": (
                self.event_date.isoformat() if self.event_date else None
            ),
            "end_date": (
                self.end_date.isoformat() if self.end_date else None
            ),
            "price": self.price,
            "capacity": self.capacity,
            "banner_url": self.banner_url,
            "tags": self.tags or [],
            "is_virtual": self.is_virtual,
            "meeting_link": self.meeting_link,
            "is_ended": self.is_ended or False,
            "ended_at": (
                self.ended_at.isoformat() if self.ended_at else None
            ),
            "registered_count": reg_count,
            "sessions_count": sess_count,
            "created_by": (
                str(self.created_by.id) if self.created_by else None
            ),
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }

    def __repr__(self) -> str:
        return f"<Event {self.title}>"
