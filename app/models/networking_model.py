"""
SkillConnect – Networking Request Model
=========================================
Manages peer-to-peer networking / connection requests between attendees.
"""

from mongoengine import (
    Document, StringField, DateTimeField, ReferenceField
)
from datetime import datetime, timezone


def now_utc():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class NetworkingRequest(Document):
    """
    A connection request from one user to another, optionally scoped to
    a specific event.

    Fields:
        sender       – User who initiated the request (required).
        receiver     – User who received the request (required).
        event        – Optional event context.
        message      – Optional personalised message.
        status       – pending | accepted | rejected.
        created_at   – Request timestamp.
        responded_at – When the receiver responded.
    """

    meta = {
        "collection": "networking_requests",
        "indexes": [
            {"fields": ["sender", "receiver", "event"], "unique": True},
        ],
        "ordering": ["-created_at"],
    }

    sender = ReferenceField("User", required=True)
    receiver = ReferenceField("User", required=True)
    event = ReferenceField("Event", null=True)
    message = StringField()
    status = StringField(
        default="pending",
        choices=["pending", "accepted", "rejected"],
    )
    created_at = DateTimeField(default=now_utc)
    responded_at = DateTimeField()

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary."""
        return {
            "id": str(self.id),
            "sender_id": (
                str(self.sender.id) if self.sender else None
            ),
            "sender_name": (
                self.sender.name if self.sender else None
            ),
            "sender_job_title": (
                self.sender.job_title if self.sender else None
            ),
            "sender_company": (
                self.sender.company if self.sender else None
            ),
            "receiver_id": (
                str(self.receiver.id) if self.receiver else None
            ),
            "receiver_name": (
                self.receiver.name if self.receiver else None
            ),
            "event_id": (
                str(self.event.id) if self.event else None
            ),
            "message": self.message,
            "status": self.status,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "responded_at": (
                self.responded_at.isoformat()
                if self.responded_at
                else None
            ),
        }

    def __repr__(self) -> str:
        return (
            f"<NetworkingRequest {self.sender.id} → "
            f"{self.receiver.id} [{self.status}]>"
        )
