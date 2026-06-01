from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
from flasgger import Swagger

load_dotenv()



db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    Swagger(app)
    # ── Configuration ──────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///skillconnect.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["RAZORPAY_KEY_ID"] = os.getenv("RAZORPAY_KEY_ID", "")
    app.config["RAZORPAY_KEY_SECRET"] = os.getenv("RAZORPAY_KEY_SECRET", "")

    # ── Extensions ─────────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)

    # ── Blueprints ─────────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.courses import courses_bp
    from app.routes.events import events_bp
    from app.routes.payments import payments_bp
    from app.routes.announcements import announcements_bp
    from app.routes.feedback import feedback_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(courses_bp, url_prefix="/courses")
    app.register_blueprint(events_bp, url_prefix="/events")
    app.register_blueprint(payments_bp, url_prefix="/payments")
    app.register_blueprint(announcements_bp, url_prefix="/announcements")
    app.register_blueprint(feedback_bp, url_prefix="/feedback")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ── Root route → serve frontend ───────────────────────────────
    @app.route("/")
    def index():
        return render_template("index.html")

    # ── Create tables ──────────────────────────────────────────────
    with app.app_context():
        from app import models  # noqa: F401 – ensures models are registered
        db.create_all()

    return app