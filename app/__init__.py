"""
SkillConnect – Application Factory
=====================================
Creates and configures the Flask application, registers blueprints,
initialises extensions (JWT, MongoDB), and mounts the index route.

Usage:
    from app import create_app
    app = create_app()
"""

from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from mongoengine import connect
from dotenv import load_dotenv
import os

# Load .env before anything else reads os.environ
load_dotenv()

# JWT extension instance – initialised inside create_app()
jwt = JWTManager()


def create_app(config_name: str = None):
    """
    Application factory.

    Args:
        config_name: Optional configuration profile name
                     ('development', 'testing', 'production').
                     Falls back to the FLASK_ENV environment variable.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # ── Load configuration ──────────────────────────────────────────────
    from config import get_config
    cfg = get_config() if config_name is None else None
    if config_name:
        from config import config_by_name
        cfg = config_by_name.get(config_name, get_config())

    app.config.from_object(cfg)

    # ── MongoDB connection (with connection pooling) ─────────────────────
    mongo_uri = app.config.get(
        "MONGODB_URI",
        os.getenv("MONGODB_URI", "mongodb://localhost:27017/skillconnect"),
    )
    connect(
        host=mongo_uri,
        maxPoolSize=20,          # max simultaneous connections
        minPoolSize=2,           # keep 2 warm connections alive
        serverSelectionTimeoutMS=3000,   # fail fast if MongoDB is down
        connectTimeoutMS=3000,
        socketTimeoutMS=10000,
    )

    # ── Initialise extensions ───────────────────────────────────────────
    jwt.init_app(app)

    # ── Register blueprints ─────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.events import events_bp
    from app.routes.sessions import sessions_bp
    from app.routes.networking import networking_bp
    from app.routes.polls import polls_bp
    from app.routes.questions import questions_bp
    from app.routes.feedback import feedback_bp
    from app.routes.announcements import announcements_bp
    from app.routes.materials import materials_bp
    from app.routes.analytics import analytics_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(events_bp, url_prefix="/events")
    app.register_blueprint(sessions_bp, url_prefix="/sessions")
    app.register_blueprint(networking_bp, url_prefix="/network")
    app.register_blueprint(polls_bp, url_prefix="/polls")
    app.register_blueprint(questions_bp, url_prefix="/questions")
    app.register_blueprint(feedback_bp, url_prefix="/feedback")
    app.register_blueprint(announcements_bp, url_prefix="/announcements")
    app.register_blueprint(materials_bp, url_prefix="/materials")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ── Front-end routes ────────────────────────────────────────────────
    @app.route("/")
    def index():
        """Serve the main landing page."""
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        """Serve the login page."""
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        """Serve the registration page."""
        return render_template("register.html")

    @app.route("/dashboard")
    def dashboard_page():
        """Serve the dashboard page."""
        return render_template("dashboard.html")

    @app.route("/browse-events")
    def events_page():
        """Serve the events browsing page."""
        return render_template("events.html")

    @app.route("/event/<event_id>")
    def event_detail_page(event_id):
        """Serve the event detail page."""
        return render_template("event_detail.html", event_id=event_id)

    @app.route("/browse-sessions")
    def sessions_page():
        """Serve the sessions browsing page."""
        return render_template("sessions.html")

    @app.route("/analytics-view")
    def analytics_page():
        """Serve the analytics dashboard page."""
        return render_template("analytics.html")

    @app.route("/admin-panel")
    def admin_page():
        """Serve the admin panel page."""
        return render_template("admin.html")

    # ── Health check ────────────────────────────────────────────────────
    @app.route("/health")
    def health():
        """Simple health-check endpoint for monitoring."""
        return {
            "status": "ok",
            "service": "skillconnect",
            "version": "2.0.0",
        }, 200

    return app