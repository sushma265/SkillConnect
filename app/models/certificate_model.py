"""
SkillConnect – Certificate Model
==================================
Stores completion certificates issued by event organizers to attendees.
Each certificate is uniquely identified by a UUID and references the
event, the recipient user, and the issuing organizer.
"""

from mongoengine import (
    Document, StringField, DateTimeField, ReferenceField, UUIDField
)
from datetime import datetime, timezone
import uuid


def now_utc():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class Certificate(Document):
    """
    Represents a completion certificate for an event.

    Fields:
        certificate_id  – Public UUID used in the shareable verify URL.
        recipient       – Reference to the attendee User.
        event           – Reference to the Event.
        issued_by       – Reference to the organizer User who issued it.
        issued_at       – Timestamp of certificate issuance.
        recipient_name  – Denormalized name at time of issue.
        event_title     – Denormalized event title at time of issue.
        organizer_name  – Denormalized organizer name at time of issue.
        event_date      – Denormalized event date string at time of issue.
    """

    meta = {
        "collection": "certificates",
        "indexes": [
            {"fields": ["recipient", "event"], "unique": True},
            {"fields": ["certificate_id"], "unique": True},
        ],
        "ordering": ["-issued_at"],
    }

    certificate_id  = StringField(required=True, unique=True)
    recipient       = ReferenceField("User", required=True)
    event           = ReferenceField("Event", required=True)
    issued_by       = ReferenceField("User", required=True)
    issued_at       = DateTimeField(default=now_utc)

    # Denormalised snapshot (so certificates survive edits/deletions)
    recipient_name  = StringField(required=True)
    event_title     = StringField(required=True)
    organizer_name  = StringField(required=True)
    event_date      = StringField()   # human-readable e.g. "15 Jun 2025"

    @staticmethod
    def generate_id() -> str:
        """Return a new unique certificate UUID string."""
        return str(uuid.uuid4())

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary of the certificate."""
        return {
            "id":             str(self.id),
            "certificate_id": self.certificate_id,
            "recipient_id":   str(self.recipient.id) if self.recipient else None,
            "recipient_name": self.recipient_name,
            "event_id":       str(self.event.id) if self.event else None,
            "event_title":    self.event_title,
            "organizer_name": self.organizer_name,
            "event_date":     self.event_date,
            "issued_at":      self.issued_at.isoformat() if self.issued_at else None,
            "issued_by_id":   str(self.issued_by.id) if self.issued_by else None,
            "verify_url":     f"/certificate/{self.certificate_id}",
        }

    def __repr__(self) -> str:
        return f"<Certificate {self.certificate_id} – {self.recipient_name} @ {self.event_title}>"
