"""
SkillConnect – Poll Model
===========================
Supports live polling during sessions.
Includes Poll, PollOption, and PollVote documents.
"""

from mongoengine import (
    Document, StringField, IntField, BooleanField,
    DateTimeField, ReferenceField
)
from datetime import datetime, timezone


def now_utc():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class PollOption(Document):
    """
    A single selectable option within a Poll.

    Fields:
        poll_id – String reference to the parent Poll ID.
        text    – Option text / label.
        order   – Display order index.
    """

    meta = {"collection": "poll_options"}

    poll_id = StringField(required=True)
    text = StringField(required=True, max_length=300)
    order = IntField(default=0)

    def to_dict(self, include_count: bool = False) -> dict:
        """Serialise the option, optionally including vote counts."""
        d = {
            "id": str(self.id),
            "poll_id": self.poll_id,
            "text": self.text,
            "order": self.order,
        }
        if include_count:
            d["vote_count"] = PollVote.objects(option=self).count()
        return d

    def __repr__(self) -> str:
        return f"<PollOption {self.text[:30]}>"


class Poll(Document):
    """
    A live poll associated with a session.

    Fields:
        session           – Parent Session reference (required).
        question          – Poll question text (required).
        is_active         – Whether the poll is still accepting votes.
        is_multiple_choice – Allow multiple selections.
        created_by        – Organiser who created the poll.
        created_at        – Creation timestamp.
        closes_at         – Optional auto-close time.
    """

    meta = {
        "collection": "polls",
        "ordering": ["created_at"],
    }

    session = ReferenceField("Session", required=True)
    question = StringField(required=True, max_length=500)
    is_active = BooleanField(default=True)
    is_multiple_choice = BooleanField(default=False)
    created_by = ReferenceField("User", required=True)
    created_at = DateTimeField(default=now_utc)
    closes_at = DateTimeField()

    def to_dict(self, include_results: bool = False) -> dict:
        """Serialise the poll with options and optional vote counts."""
        options = PollOption.objects(
            poll_id=str(self.id)
        ).order_by("order")
        total_votes = PollVote.objects(poll=self).count()

        return {
            "id": str(self.id),
            "session_id": (
                str(self.session.id) if self.session else None
            ),
            "question": self.question,
            "is_active": self.is_active,
            "is_multiple_choice": self.is_multiple_choice,
            "created_by": (
                str(self.created_by.id) if self.created_by else None
            ),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "closes_at": (
                self.closes_at.isoformat()
                if self.closes_at
                else None
            ),
            "options": [
                o.to_dict(include_count=include_results)
                for o in options
            ],
            "total_votes": total_votes,
        }

    def __repr__(self) -> str:
        return f"<Poll {self.question[:40]}>"


class PollVote(Document):
    """
    A single vote cast by a user on a poll option.

    Unique constraint: (poll, option, user) prevents duplicate votes.
    """

    meta = {
        "collection": "poll_votes",
        "indexes": [
            {"fields": ["poll", "option", "user"], "unique": True},
        ],
    }

    poll = ReferenceField("Poll", required=True)
    option = ReferenceField("PollOption", required=True)
    user = ReferenceField("User", required=True)
    created_at = DateTimeField(default=now_utc)

    def to_dict(self) -> dict:
        """Serialise the vote."""
        return {
            "id": str(self.id),
            "poll_id": str(self.poll.id) if self.poll else None,
            "option_id": (
                str(self.option.id) if self.option else None
            ),
            "user_id": str(self.user.id) if self.user else None,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }

    def __repr__(self) -> str:
        return f"<PollVote poll={self.poll.id} user={self.user.id}>"
