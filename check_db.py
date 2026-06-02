"""
check_db.py -- SkillConnect MongoDB Health & Schema Verification
Run: python check_db.py
"""
import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app import create_app

app = create_app()
PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"
SEP = "=" * 60


def check_db():
    print("\n" + SEP)
    print("  SkillConnect -- MongoDB Verification")
    print(SEP)
    all_ok = True

    # Import models
    try:
        from app.models import (User, Course, Event, Registration, Payment,
                                 Announcement, Feedback, Session, SessionMaterial,
                                 Question, Poll, PollOption, PollVote, NetworkingRequest)
        print(f"\n  {PASS} All 13 models imported successfully")
    except Exception as e:
        print(f"\n  {FAIL} Model import failed: {e}")
        sys.exit(1)

    # Collection counts
    print("\n  COLLECTION COUNTS")
    print("  " + "-" * 40)
    collections = [
        ("users", User), ("courses", Course), ("events", Event),
        ("registrations", Registration), ("payments", Payment),
        ("announcements", Announcement), ("feedback", Feedback),
        ("sessions", Session), ("session_materials", SessionMaterial),
        ("questions", Question), ("polls", Poll),
        ("poll_options", PollOption), ("poll_votes", PollVote),
        ("networking_requests", NetworkingRequest),
    ]
    for name, model in collections:
        try:
            count = model.objects.count()
            print(f"  {PASS} {name:30s}  {count:>6} docs")
        except Exception as e:
            print(f"  {FAIL} {name:30s}  ERROR: {e}")
            all_ok = False

    # CRUD smoke test
    print("\n  CRUD SMOKE TEST")
    print("  " + "-" * 40)
    import secrets as _s
    test_email = f"dbcheck_{_s.token_hex(4)}@test.local"
    try:
        u = User(name="DB Check User", email=test_email, role="user")
        u.set_password("testpass")
        u.save()
        fetched = User.objects(email=test_email).first()
        assert fetched is not None
        assert fetched.name == "DB Check User"
        fetched.delete()
        assert User.objects(email=test_email).first() is None
        print(f"  {PASS} User CRUD (INSERT, SELECT, DELETE)  OK")
    except Exception as e:
        print(f"  {FAIL} User CRUD failed: {e}")
        all_ok = False

    # QR token test
    try:
        reg = Registration()
        reg.generate_qr_token()
        assert reg.qr_token and len(reg.qr_token) > 10
        print(f"  {PASS} QR token generation  OK  (sample: {reg.qr_token[:12]}...)")
    except Exception as e:
        print(f"  {FAIL} QR token test failed: {e}")
        all_ok = False

    # Unique index test
    try:
        u1 = User(name="Test A", email=f"uniq_{_s.token_hex(4)}@test.local", role="user")
        u1.set_password("x"); u1.save()
        u2 = User(name="Test B", email=u1.email, role="user")
        u2.set_password("x")
        try:
            u2.save()
            u2.delete()
            print(f"  {FAIL} Unique constraint NOT enforced on email")
            all_ok = False
        except Exception:
            print(f"  {PASS} Unique email constraint enforced  OK")
        u1.delete()
    except Exception as e:
        print(f"  {FAIL} Unique constraint test failed: {e}")
        all_ok = False

    print("\n" + SEP)
    if all_ok:
        print(f"  {PASS}  ALL CHECKS PASSED -- MongoDB is healthy!")
    else:
        print(f"  {FAIL}  SOME CHECKS FAILED -- Review errors above.")
        sys.exit(1)
    print(SEP + "\n")


if __name__ == "__main__":
    check_db()
