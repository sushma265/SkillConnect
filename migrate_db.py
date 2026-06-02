"""
migrate_db.py -- SkillConnect Column Migration Script
Adds new columns to existing tables without losing data.
Run: python migrate_db.py
"""
import sys

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app import create_app, db

app = create_app()

# Map: table -> list of (column_name, column_def_sql)
MIGRATIONS = {
    "users": [
        ("google_id",    "VARCHAR(128) UNIQUE"),
        ("bio",          "TEXT"),
        ("company",      "VARCHAR(150)"),
        ("job_title",    "VARCHAR(150)"),
        ("linkedin_url", "VARCHAR(300)"),
        ("avatar_url",   "VARCHAR(500)"),
    ],
    "events": [
        ("end_date",     "DATETIME"),
        ("banner_url",   "VARCHAR(500)"),
        ("tags",         "VARCHAR(500)"),
        ("is_virtual",   "BOOLEAN DEFAULT 0"),
        ("meeting_link", "VARCHAR(500)"),
    ],
    "registrations": [
        ("qr_token",      "VARCHAR(64)"),
        ("checked_in",    "BOOLEAN DEFAULT 0"),
        ("checked_in_at", "DATETIME"),
    ],
    "announcements": [
        ("event_id",     "INTEGER REFERENCES events(id)"),
        ("priority",     "VARCHAR(20) DEFAULT 'medium'"),
        ("is_published", "BOOLEAN DEFAULT 1"),
    ],
    "feedback": [
        ("session_id", "INTEGER REFERENCES sessions(id)"),
    ],
}


def migrate():
    PASS = "[PASS]"
    FAIL = "[FAIL]"
    INFO = "[INFO]"

    with app.app_context():
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)

        print("\n" + "=" * 60)
        print("  SkillConnect -- Column Migration")
        print("=" * 60 + "\n")

        for table, columns in MIGRATIONS.items():
            existing_cols = {c["name"] for c in inspector.get_columns(table)} if table in inspector.get_table_names() else set()

            for col_name, col_def in columns:
                if col_name in existing_cols:
                    print(f"  {INFO} {table}.{col_name:20s}  already exists, skipped")
                else:
                    try:
                        sql = f'ALTER TABLE "{table}" ADD COLUMN "{col_name}" {col_def}'
                        db.session.execute(text(sql))
                        db.session.commit()
                        print(f"  {PASS} {table}.{col_name:20s}  ADDED")
                    except Exception as e:
                        db.session.rollback()
                        print(f"  {FAIL} {table}.{col_name:20s}  ERROR: {e}")

        print("\n" + "=" * 60)
        print("  Migration complete!")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    migrate()
