"""
SkillConnect – Question Model
================================
Supports Q&A during sessions with upvoting, anonymous posting, and
organiser answers.
"""

from mongoengine import (
    Document, StringField, IntField, BooleanField,
    DateTimeField, ReferenceField, ListField
)
from datetime import datetime, timezone


def now_utc():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class Question(Document):
    """
    A question asked during a session.

    Fields:
        session      – Parent Session reference (required).
        user         – The user who asked the question (required).
        content      – Question text (required).
        upvotes      – Number of upvotes.
        is_answered  – Whether the question has been answered.
        is_anonymous – Whether the user wishes to remain anonymous.
        answer       – Organiser's answer text.
        answered_by  – User who answered.
        answered_at  – When the answer was given.
        upvoted_by   – List of users who upvoted (prevents duplicates).
        created_at   – Submission timestamp.
    """

    meta = {
        "collection": "questions",
        "ordering": ["-upvotes", "created_at"],
    }

    session = ReferenceField("Session", required=True)
    user = ReferenceField("User", required=True)
    content = StringField(required=True)
    upvotes = IntField(default=0)
    is_answered = BooleanField(default=False)
    is_anonymous = BooleanField(default=False)
    answer = StringField()
    answered_by = ReferenceField("User", null=True)
    answered_at = DateTimeField()
    upvoted_by = ListField(ReferenceField("User"))
    created_at = DateTimeField(default=now_utc)

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary."""
        return {
            "id": str(self.id),
            "session_id": (
                str(self.session.id) if self.session else None
            ),
            "user_id": (
                str(self.user.id)
                if self.user and not self.is_anonymous
                else None
            ),
            "user_name": (
                self.user.name
                if self.user and not self.is_anonymous
                else "Anonymous"
            ),
            "content": self.content,
            "upvotes": self.upvotes,
            "is_answered": self.is_answered,
            "is_anonymous": self.is_anonymous,
            "answer": self.answer,
            "answered_by": (
                str(self.answered_by.id)
                if self.answered_by
                else None
            ),
            "answered_at": (
                self.answered_at.isoformat()
                if self.answered_at
                else None
            ),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }

    def __repr__(self) -> str:
        return f"<Question {self.content[:40]}>"
