"""
SkillConnect – Models Package
==============================
Re-exports all MongoEngine document classes for convenient imports.

Usage:
    from app.models import User, Event, Session, Registration, ...
"""

from app.models.user_model import User
from app.models.event_model import Event
from app.models.session_model import Session
from app.models.registration_model import Registration
from app.models.networking_model import NetworkingRequest
from app.models.poll_model import Poll, PollOption, PollVote
from app.models.question_model import Question
from app.models.feedback_model import Feedback
from app.models.announcement_model import Announcement
from app.models.material_model import SessionMaterial
from app.models.certificate_model import Certificate

__all__ = [
    "User",
    "Event",
    "Session",
    "Registration",
    "NetworkingRequest",
    "Poll",
    "PollOption",
    "PollVote",
    "Question",
    "Feedback",
    "Announcement",
    "SessionMaterial",
    "Certificate",
]
