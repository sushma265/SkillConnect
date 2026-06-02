"""
SkillConnect – Session Model
==============================
Represents individual sessions within an event (keynotes, panels,
workshops, networking breaks).
"""

from mongoengine import (
    Document, StringField, BooleanField, DateTimeField, ReferenceField
)
from datetime import datetime, timezone


def now_utc():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class Session(Document):
    """
    An individual session (talk, panel, workshop, break) within an Event.

    Fields:
        event             – Parent Event reference (required).
        title             – Session title (required).
        description       – Session description.
        speaker_name      – Name of the speaker / facilitator.
        speaker_bio       – Short biography of the speaker.
        speaker_avatar_url – Avatar URL for the speaker.
        session_type      – keynote | panel | workshop | networking | break.
        room              – Room or virtual room name.
        starts_at         – Session start time (required).
        ends_at           – Session end time (required).
        is_live           – Whether the session is currently live.
        stream_url        – Live-stream or recording URL.
        created_by        – Organiser who created the session.
        created_at        – Creation timestamp.
    """

    meta = {
        "collection": "sessions",
        "ordering": ["starts_at"],
    }

    event = ReferenceField("Event", required=True)
    title = StringField(required=True, max_length=200)
    description = StringField()
    speaker_name = StringField()
    speaker_bio = StringField()
    speaker_avatar_url = StringField()
    session_type = StringField(
        default="keynote",
        choices=["keynote", "panel", "workshop", "networking", "break"],
    )
    room = StringField()
    starts_at = DateTimeField(required=True)
    ends_at = DateTimeField(required=True)
    is_live = BooleanField(default=False)
    stream_url = StringField()
    created_by = ReferenceField("User", required=True)
    created_at = DateTimeField(default=now_utc)

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary of the session."""
        from app.models.material_model import SessionMaterial
        from app.models.question_model import Question
        from app.models.poll_model import Poll

        mat_count = SessionMaterial.objects(session=self).count()
        q_count = Question.objects(session=self).count()
        poll_count = Poll.objects(session=self).count()

        return {
            "id": str(self.id),
            "event_id": (
                str(self.event.id) if self.event else None
            ),
            "title": self.title,
            "description": self.description,
            "speaker_name": self.speaker_name,
            "speaker_bio": self.speaker_bio,
            "speaker_avatar_url": self.speaker_avatar_url,
            "session_type": self.session_type,
            "room": self.room,
            "starts_at": (
                self.starts_at.isoformat() if self.starts_at else None
            ),
            "ends_at": (
                self.ends_at.isoformat() if self.ends_at else None
            ),
            "is_live": self.is_live,
            "stream_url": self.stream_url,
            "materials_count": mat_count,
            "questions_count": q_count,
            "polls_count": poll_count,
            "created_by": (
                str(self.created_by.id) if self.created_by else None
            ),
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }

    def __repr__(self) -> str:
        return f"<Session {self.title}>"
