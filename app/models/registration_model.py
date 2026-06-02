"""
SkillConnect – Registration Model
====================================
Tracks event registrations, QR tokens for check-in, and check-in status.
"""

from mongoengine import (
    Document, StringField, BooleanField, DateTimeField, ReferenceField
)
from datetime import datetime, timezone
import secrets


def now_utc():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class Registration(Document):
    """
    Tracks a user's registration for a specific event.

    Fields:
        user          – The registered attendee (required).
        event         – The event being registered for (required).
        status        – pending | confirmed | cancelled.
        registered_at – Timestamp of registration.
        qr_token      – Unique token for QR check-in.
        checked_in    – Whether the attendee has checked in.
        checked_in_at – Timestamp of check-in.
    """

    meta = {
        "collection": "registrations",
        "indexes": [
            {"fields": ["user", "event"], "unique": True},
        ],
        "ordering": ["-registered_at"],
    }

    user = ReferenceField("User", required=True)
    event = ReferenceField("Event", required=True)
    status = StringField(
        default="pending",
        choices=["pending", "confirmed", "cancelled"],
    )
    registered_at = DateTimeField(default=now_utc)
    qr_token = StringField(unique=True, sparse=True)
    checked_in = BooleanField(default=False)
    checked_in_at = DateTimeField()

    def generate_qr_token(self) -> str:
        """Generate a cryptographically-secure QR token."""
        self.qr_token = secrets.token_urlsafe(32)
        return self.qr_token

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary of the registration."""
        return {
            "id": str(self.id),
            "user_id": str(self.user.id) if self.user else None,
            "event_id": str(self.event.id) if self.event else None,
            "event_title": (
                self.event.title if self.event else None
            ),
            "status": self.status,
            "registered_at": (
                self.registered_at.isoformat()
                if self.registered_at
                else None
            ),
            "qr_token": self.qr_token,
            "checked_in": self.checked_in,
            "checked_in_at": (
                self.checked_in_at.isoformat()
                if self.checked_in_at
                else None
            ),
        }

    def __repr__(self) -> str:
        return (
            f"<Registration user={self.user.id} "
            f"event={self.event.id} status={self.status}>"
        )
