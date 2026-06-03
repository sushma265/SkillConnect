"""
SkillConnect – User Model
==========================
Stores registered users with role-based access control.
Roles: attendee, organizer, admin.
Supports both local password auth and Google OAuth.
"""

from mongoengine import (
    Document, StringField, BooleanField, DateTimeField
)
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# Use pbkdf2 (fast + NIST-compliant). Werkzeug 3 defaults to scrypt which
# takes ~130ms per hash. pbkdf2:sha256:260000 takes ~30ms – 4x faster.
_HASH_METHOD = "pbkdf2:sha256:260000"


def now_utc():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class User(Document):
    """
    Represents a platform user.

    Fields:
        name        – Display name (required).
        email       – Unique email address (required, indexed).
        password_hash – Bcrypt hash of the user's password.
        google_id   – Google subject identifier (sparse unique).
        role        – One of 'attendee', 'organizer', 'admin'.
        is_active   – Soft-delete / deactivation flag.
        bio         – Short biography.
        company     – Company or organisation name.
        job_title   – Professional title.
        linkedin_url – LinkedIn profile link.
        avatar_url  – Profile picture URL.
        created_at  – Account creation timestamp.
    """

    meta = {
        "collection": "users",
        "indexes": [
            {"fields": ["email"], "unique": True},   # fast O(log n) lookup at login
            {"fields": ["google_id"], "unique": True, "sparse": True},
        ],
        "ordering": ["-created_at"],
    }

    name = StringField(required=True, max_length=100)
    email = StringField(required=True, unique=True, max_length=150)
    password_hash = StringField(required=True)
    google_id = StringField(unique=True, sparse=True)
    role = StringField(
        default="attendee",
        choices=["attendee", "organizer", "admin"],
    )
    is_active = BooleanField(default=True)
    bio = StringField()
    company = StringField()
    job_title = StringField()
    linkedin_url = StringField()
    avatar_url = StringField()
    created_at = DateTimeField(default=now_utc)

    # ── Password helpers ────────────────────────────────────────────────

    def set_password(self, password: str) -> None:
        """Hash and store a plaintext password using pbkdf2:sha256."""
        self.password_hash = generate_password_hash(
            password, method=_HASH_METHOD, salt_length=16
        )

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        # Short-circuit for OAuth-only accounts (no real password)
        if not self.password_hash or self.password_hash == "oauth-no-password":
            return False
        return check_password_hash(self.password_hash, password)

    # ── Serialisation ───────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary of the user."""
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "bio": self.bio,
            "company": self.company,
            "job_title": self.job_title,
            "linkedin_url": self.linkedin_url,
            "avatar_url": self.avatar_url,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"
