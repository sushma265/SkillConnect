from app import db
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash


# ── Helper ─────────────────────────────────────────────────────────────────
def now_utc():
    return datetime.now(timezone.utc)


# ══════════════════════════════════════════════════════════════════════════════
# User
# ══════════════════════════════════════════════════════════════════════════════
class User(db.Model):
    __tablename__ = "users"
    google_id = db.Column(db.String(128), unique=True, nullable=True)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # role: "user" | "conductor" | "admin"
    role = db.Column(db.String(20), nullable=False, default="user")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_utc)

    # relationships
    registrations = db.relationship("Registration", back_populates="user", lazy=True)
    payments = db.relationship("Payment", back_populates="user", lazy=True)
    feedbacks = db.relationship("Feedback", back_populates="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# Course
# ══════════════════════════════════════════════════════════════════════════════
class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)           # in INR
    duration = db.Column(db.String(50))                  # e.g. "6 weeks"
    instructor = db.Column(db.String(100))
    category = db.Column(db.String(100))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc)
    updated_at = db.Column(db.DateTime, default=now_utc, onupdate=now_utc)

    # relationships
    feedbacks = db.relationship("Feedback", back_populates="course", lazy=True)
    payments = db.relationship("Payment", back_populates="course", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "duration": self.duration,
            "instructor": self.instructor,
            "category": self.category,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# Event / Workshop
# ══════════════════════════════════════════════════════════════════════════════
class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(50), default="event")   # "event" | "workshop"
    venue = db.Column(db.String(200))
    event_date = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, default=0.0)                 # 0 = free
    capacity = db.Column(db.Integer, default=100)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc)
    updated_at = db.Column(db.DateTime, default=now_utc, onupdate=now_utc)

    # relationships
    registrations = db.relationship("Registration", back_populates="event", lazy=True)
    feedbacks = db.relationship("Feedback", back_populates="event", lazy=True)
    payments = db.relationship("Payment", back_populates="event", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "venue": self.venue,
            "event_date": self.event_date.isoformat(),
            "price": self.price,
            "capacity": self.capacity,
            "registered_count": len(self.registrations),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# Registration  (user ↔ event)
# ══════════════════════════════════════════════════════════════════════════════
class Registration(db.Model):
    __tablename__ = "registrations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    # status: "pending" | "confirmed" | "cancelled"
    status = db.Column(db.String(20), default="pending")
    registered_at = db.Column(db.DateTime, default=now_utc)

    # relationships
    user = db.relationship("User", back_populates="registrations")
    event = db.relationship("Event", back_populates="registrations")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "event_title": self.event.title if self.event else None,
            "status": self.status,
            "registered_at": self.registered_at.isoformat(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# Payment
# ══════════════════════════════════════════════════════════════════════════════
class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # only one of the two foreign keys will be set
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=True)

    razorpay_order_id = db.Column(db.String(100), unique=True, nullable=False)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    razorpay_signature = db.Column(db.String(256), nullable=True)

    amount = db.Column(db.Float, nullable=False)           # in INR
    currency = db.Column(db.String(10), default="INR")
    # status: "created" | "paid" | "failed"
    status = db.Column(db.String(20), default="created")
    payment_type = db.Column(db.String(20))                # "course" | "event"
    created_at = db.Column(db.DateTime, default=now_utc)
    paid_at = db.Column(db.DateTime, nullable=True)

    # relationships
    user = db.relationship("User", back_populates="payments")
    course = db.relationship("Course", back_populates="payments")
    event = db.relationship("Event", back_populates="payments")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "event_id": self.event_id,
            "razorpay_order_id": self.razorpay_order_id,
            "razorpay_payment_id": self.razorpay_payment_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "payment_type": self.payment_type,
            "created_at": self.created_at.isoformat(),
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# Announcement
# ══════════════════════════════════════════════════════════════════════════════
class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# Feedback
# ══════════════════════════════════════════════════════════════════════════════
class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # only one of the two foreign keys will be set

    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=True)

    rating = db.Column(db.Integer, nullable=False)        # 1–5
    comment = db.Column(db.Text)
    feedback_type = db.Column(db.String(20))              # "course" | "event"
    created_at = db.Column(db.DateTime, default=now_utc)

    # relationships
    user = db.relationship("User", back_populates="feedbacks")
    course = db.relationship("Course", back_populates="feedbacks")
    event = db.relationship("Event", back_populates="feedbacks")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "event_id": self.event_id,
            "rating": self.rating,
            "comment": self.comment,
            "feedback_type": self.feedback_type,
            "created_at": self.created_at.isoformat(),
        }
