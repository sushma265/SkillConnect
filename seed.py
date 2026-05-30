"""
seed.py – Populate the database with sample data for testing.
Run once after starting fresh:  python seed.py
"""
from app import create_app, db
from app.models import User, Course, Event, Announcement

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # ── Users ──────────────────────────────────────────────────────
    admin = User(name="Admin User", email="admin@skillconnect.com", role="admin")
    admin.set_password("admin123")

    conductor = User(name="Jane Conductor", email="jane@skillconnect.com", role="conductor")
    conductor.set_password("conductor123")

    user1 = User(name="John Doe", email="john@example.com", role="user")
    user1.set_password("user123")

    db.session.add_all([admin, conductor, user1])
    db.session.commit()

    # ── Courses ────────────────────────────────────────────────────
    c1 = Course(
        title="Python for Beginners",
        description="Learn Python from scratch with hands-on exercises.",
        price=999.00,
        duration="4 weeks",
        instructor="Jane Conductor",
        category="Programming",
        created_by=conductor.id,
    )
    c2 = Course(
        title="Web Development Bootcamp",
        description="HTML, CSS, JavaScript and Flask – all in one course.",
        price=1499.00,
        duration="8 weeks",
        instructor="Jane Conductor",
        category="Web",
        created_by=conductor.id,
    )
    db.session.add_all([c1, c2])

    # ── Events ─────────────────────────────────────────────────────
    from datetime import datetime
    e1 = Event(
        title="AI & ML Workshop",
        description="Hands-on workshop on Machine Learning fundamentals.",
        event_type="workshop",
        venue="Seminar Hall A",
        event_date=datetime(2025, 8, 15, 10, 0),
        price=299.00,
        capacity=50,
        created_by=conductor.id,
    )
    e2 = Event(
        title="Open Source Day",
        description="Free event celebrating open source contributions.",
        event_type="event",
        venue="Main Auditorium",
        event_date=datetime(2025, 9, 1, 9, 0),
        price=0.0,
        capacity=200,
        created_by=conductor.id,
    )
    db.session.add_all([e1, e2])

    # ── Announcements ──────────────────────────────────────────────
    ann = Announcement(
        title="Platform Launch!",
        content="Welcome to SkillConnect – your one-stop hub for skill development.",
        created_by=admin.id,
    )
    db.session.add(ann)
    db.session.commit()

    print("✅ Database seeded successfully!")
    print("──────────────────────────────────────")
    print("Admin    : admin@skillconnect.com   / admin123")
    print("Conductor: jane@skillconnect.com    / conductor123")
    print("User     : john@example.com         / user123")
