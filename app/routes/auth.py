"""
SkillConnect – Authentication Routes
========================================
Handles user registration, login (email + password), token refresh,
current-user retrieval, and Google OAuth 2.0 flow.
"""

from flask import (
    Blueprint, request, jsonify, redirect,
    session as flask_session,
)
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity,
)
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
import os

from app.models.user_model import User
from app.utils.jwt_utils import get_current_user

auth_bp = Blueprint("auth", __name__)

# ── Google OAuth settings ───────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:5000/auth/google/callback",
    "https://skillconnect-12m0.onrender.com/auth/google/callback",
)
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def _make_flow():
    """Build a Google OAuth Flow from environment credentials."""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )


# ── POST /auth/register ────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user with email and password.
    ---
    tags: [Authentication]
    consumes: [application/json]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, email, password]
          properties:
            name:     {type: string, example: Jane Doe}
            email:    {type: string, example: jane@example.com}
            password: {type: string, example: SecurePass123}
            role:     {type: string, example: attendee}
    responses:
      201: {description: Account created}
      409: {description: Email already registered}
    """
    data = request.get_json()

    # Validate required fields
    for field in ["name", "email", "password"]:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    # Check for existing email (only fetch the id – fastest possible check)
    if User.objects(email=data["email"]).only("id").first():
        return jsonify({"error": "Email already registered"}), 409

    # Validate role
    role = data.get("role", "attendee")
    if role not in ["attendee", "organizer"]:
        return jsonify({
            "error": "Role must be 'attendee' or 'organizer'"
        }), 400

    # Create user
    user = User(name=data["name"], email=data["email"], role=role)
    user.set_password(data["password"])
    user.save()

    # Generate tokens
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "name": user.name},
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message": "Account created successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
    }), 201


# ── POST /auth/login ───────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate with email and password.
    ---
    tags: [Authentication]
    consumes: [application/json]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email:    {type: string}
            password: {type: string}
    responses:
      200: {description: Login successful}
      401: {description: Invalid credentials}
    """
    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify({
            "error": "Email and password are required"
        }), 400

    user = User.objects(email=data["email"]).only(
        "id", "email", "password_hash", "role", "name", "is_active",
        "avatar_url", "bio", "company", "job_title", "linkedin_url",
        "created_at",
    ).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({
            "error": "Account is deactivated. Contact admin."
        }), 403

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "name": user.name},
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
    }), 200


# ── POST /auth/refresh ─────────────────────────────────────────────────
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh an expired access token using a valid refresh token.
    ---
    tags: [Authentication]
    security: [{Bearer: []}]
    responses:
      200: {description: New access token}
    """
    current_user_id = get_jwt_identity()
    user = User.objects(id=current_user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    new_access = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "name": user.name},
    )
    return jsonify({"access_token": new_access}), 200


# ── GET /auth/me ────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Get the currently-authenticated user's profile.
    ---
    tags: [Authentication]
    security: [{Bearer: []}]
    responses:
      200: {description: Current user}
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


# ── GET /auth/google ────────────────────────────────────────────────────
@auth_bp.route("/google", methods=["GET"])
def google_login():
    """
    Initiate Google OAuth 2.0 login flow.
    Redirects the user to Google's consent screen.
    """
    flow = _make_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="select_account",
    )
    flask_session["oauth_state"] = state
    return redirect(auth_url)


# ── GET /auth/google/callback ──────────────────────────────────────────
@auth_bp.route("/google/callback", methods=["GET"])
def google_callback():
    """
    Handle Google OAuth callback.
    Exchanges the authorisation code for tokens, creates or
    updates the user, and redirects to the frontend with a JWT.
    """
    error = request.args.get("error")
    if error:
        return redirect(f"/?auth_error={error}")

    # Validate state parameter
    if request.args.get("state") != flask_session.get("oauth_state"):
        return redirect("/?auth_error=state_mismatch")

    # Exchange authorisation code for tokens
    try:
        flow = _make_flow()
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
    except Exception:
        return redirect("/?auth_error=token_exchange_failed")

    # Verify the ID token
    try:
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError:
        return redirect("/?auth_error=invalid_token")

    google_id = id_info.get("sub")
    email = id_info.get("email")
    name = id_info.get("name") or email.split("@")[0]

    if not email:
        return redirect("/?auth_error=no_email")

    # Find or create user
    user = User.objects(email=email).first()
    if user:
        if not user.google_id:
            user.google_id = google_id
            user.save()
    else:
        user = User(
            name=name,
            email=email,
            role="attendee",
            google_id=google_id,
        )
        user.password_hash = "oauth-no-password"
        if id_info.get("picture"):
            user.avatar_url = id_info["picture"]
        user.save()

    if not user.is_active:
        return redirect("/?auth_error=account_deactivated")

    # Issue JWT and redirect to frontend
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "name": user.name},
    )
    frontend_url = os.environ.get(
        "FRONTEND_URL", "http://localhost:5000"
    )
    return redirect(
        f"{frontend_url}/?sc_token={access_token}"
        f"&sc_user_id={user.id}"
    )