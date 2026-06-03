"""
SkillConnect – Configuration Module
====================================
Centralized configuration management for the SkillConnect platform.
Supports development, testing, and production environments via environment
variables.  Secrets (MongoDB URI, Google OAuth credentials, JWT keys) are
loaded from a `.env` file or system environment.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()


class Config:
    """Base configuration shared across all environments."""

    # ── Flask Core ──────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    DEBUG = False
    TESTING = False

    # ── MongoDB Atlas / Local ───────────────────────────────────────────
    MONGODB_URI = os.getenv(
        "MONGODB_URI",
        "mongodb://localhost:27017/skillconnect",
    )

    # ── JWT Settings ────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_HOURS", "24"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_DAYS", "30"))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # ── Google OAuth 2.0 ────────────────────────────────────────────────
    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:5000/auth/google/callback",
        "https://skillconnect-12m0.onrender.com/auth/google/callback",
    )

    # ── Frontend URL (used for OAuth redirect after login) ──────────────
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5000")

    # ── File Uploads ────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "uploads"
    )

    # ── QR Code ─────────────────────────────────────────────────────────
    QR_CODE_VERSION = 1
    QR_CODE_BOX_SIZE = 10
    QR_CODE_BORDER = 4


class DevelopmentConfig(Config):
    """Development-specific configuration."""

    DEBUG = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=72)  # Longer for dev


class TestingConfig(Config):
    """Testing-specific configuration."""

    TESTING = True
    MONGODB_URI = os.getenv(
        "TEST_MONGODB_URI",
        "mongodb://localhost:27017/skillconnect_test",
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


class ProductionConfig(Config):
    """Production-specific configuration."""

    DEBUG = False
    # In production these MUST be set via environment variables
    # SECRET_KEY, JWT_SECRET_KEY, MONGODB_URI, GOOGLE_OAUTH_*


# ── Configuration Registry ──────────────────────────────────────────────
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Return the active configuration class based on FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development").lower()
    return config_by_name.get(env, DevelopmentConfig)
