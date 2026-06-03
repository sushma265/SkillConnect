"""
SkillConnect – Authentication Routes
========================================
Advanced authentication system with:
- Register/Login
- JWT Authentication
- Google OAuth
- Forgot Password
- Reset Password
- Logout
- Change Password
- User Session Management
"""

from flask import (
    Blueprint,
    request,
    jsonify,
    redirect,
    session as flask_session,
)

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow

from datetime import datetime, timezone
import secrets
import os

from app.models.user_model import User
from app.utils.jwt_utils import get_current_user

auth_bp = Blueprint("auth", __name__)


# ═════════════════════════════════════════════════════════════
# GOOGLE OAUTH CONFIG
# ═════════════════════════════════════════════════════════════

GOOGLE_CLIENT_ID = os.environ.get(
    "GOOGLE_CLIENT_ID"
)

GOOGLE_CLIENT_SECRET = os.environ.get(
    "GOOGLE_CLIENT_SECRET"
)

GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:5000/auth/google/callback"
)

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def _make_flow():

    return Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri":
                    "https://accounts.google.com/o/oauth2/auth",
                "token_uri":
                    "https://oauth2.googleapis.com/token",
                "redirect_uris": [
                    GOOGLE_REDIRECT_URI
                ],
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )


# ═════════════════════════════════════════════════════════════
# REGISTER
# ═════════════════════════════════════════════════════════════

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register new account
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    responses:
      201:
        description: Account created
    """

    data = request.get_json()

    required_fields = [
        "name",
        "email",
        "password"
    ]

    for field in required_fields:

        if not data.get(field):
            return jsonify({
                "error": f"{field} is required"
            }), 400

    email = data["email"].strip().lower()

    existing_user = User.objects(
        email=email
    ).first()

    if existing_user:
        return jsonify({
            "error": "Email already registered"
        }), 409

    role = data.get(
        "role",
        "attendee"
    )

    if role not in (
        "attendee",
        "organizer"
    ):
        return jsonify({
            "error": "Invalid role"
        }), 400

    user = User(
        name=data["name"],
        email=email,
        role=role,
    )

    user.set_password(
        data["password"]
    )

    user.created_at = datetime.now(
        timezone.utc
    )

    user.save()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "name": user.name
        }
    )

    refresh_token = create_refresh_token(
        identity=str(user.id)
    )

    return jsonify({
        "message": "Account created successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    }), 201


# ═════════════════════════════════════════════════════════════
# LOGIN
# ═════════════════════════════════════════════════════════════

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login user
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    responses:
      200:
        description: Login successful
    """

    data = request.get_json()

    email = data.get(
        "email",
        ""
    ).strip().lower()

    password = data.get(
        "password",
        ""
    )

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    user = User.objects(
        email=email
    ).first()

    if not user or not user.check_password(password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    if not user.is_active:
        return jsonify({
            "error": "Account deactivated"
        }), 403

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "name": user.name
        }
    )

    refresh_token = create_refresh_token(
        identity=str(user.id)
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# REFRESH TOKEN
# ═════════════════════════════════════════════════════════════

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():

    """
    Refresh access token
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    """

    user_id = get_jwt_identity()

    user = User.objects(
        id=user_id
    ).first()

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    new_access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "name": user.name
        }
    )

    return jsonify({
        "access_token": new_access_token
    }), 200


# ═════════════════════════════════════════════════════════════
# CURRENT USER
# ═════════════════════════════════════════════════════════════

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Get current user
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    """

    user = get_current_user()

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify({
        "user": user.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# CHANGE PASSWORD
# ═════════════════════════════════════════════════════════════

@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    """
    Change account password
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    """

    user = get_current_user()

    data = request.get_json()

    current_password = data.get(
        "current_password"
    )

    new_password = data.get(
        "new_password"
    )

    if not current_password or not new_password:
        return jsonify({
            "error": "Both passwords required"
        }), 400

    if not user.check_password(
        current_password
    ):
        return jsonify({
            "error": "Current password incorrect"
        }), 401

    user.set_password(
        new_password
    )

    user.save()

    return jsonify({
        "message": "Password updated successfully"
    }), 200


# ═════════════════════════════════════════════════════════════
# FORGOT PASSWORD
# ═════════════════════════════════════════════════════════════

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    Generate reset token
    ---
    tags:
      - Authentication
    """

    data = request.get_json()

    email = data.get(
        "email",
        ""
    ).strip().lower()

    user = User.objects(
        email=email
    ).first()

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    reset_token = secrets.token_hex(32)

    user.reset_token = reset_token
    user.reset_token_created_at = datetime.now(
        timezone.utc
    )

    user.save()

    return jsonify({
        "message": "Password reset token generated",
        "reset_token": reset_token
    }), 200


# ═════════════════════════════════════════════════════════════
# RESET PASSWORD
# ═════════════════════════════════════════════════════════════

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """
    Reset password using token
    ---
    tags:
      - Authentication
    """

    data = request.get_json()

    token = data.get("token")
    password = data.get("new_password")

    if not token or not password:
        return jsonify({
            "error": "Token and password required"
        }), 400

    user = User.objects(
        reset_token=token
    ).first()

    if not user:
        return jsonify({
            "error": "Invalid token"
        }), 400

    user.set_password(password)

    user.reset_token = None

    user.save()

    return jsonify({
        "message": "Password reset successful"
    }), 200


# ═════════════════════════════════════════════════════════════
# LOGOUT
# ═════════════════════════════════════════════════════════════

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Logout user
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    """

    return jsonify({
        "message": "Logout successful"
    }), 200


# ═════════════════════════════════════════════════════════════
# GOOGLE LOGIN
# ═════════════════════════════════════════════════════════════

@auth_bp.route("/google", methods=["GET"])
def google_login():
    """
    Start Google OAuth
    ---
    tags:
      - Google OAuth
    """

    flow = _make_flow()

    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="select_account"
    )

    flask_session["oauth_state"] = state

    return redirect(auth_url)


# ═════════════════════════════════════════════════════════════
# GOOGLE CALLBACK
# ═════════════════════════════════════════════════════════════

@auth_bp.route("/google/callback", methods=["GET"])
def google_callback():
    """
    Google OAuth callback
    ---
    tags:
      - Google OAuth
    """

    error = request.args.get("error")

    if error:
        return redirect(
            f"/?auth_error={error}"
        )

    if (
        request.args.get("state")
        != flask_session.get("oauth_state")
    ):
        return redirect(
            "/?auth_error=state_mismatch"
        )

    try:

        flow = _make_flow()

        flow.fetch_token(
            authorization_response=request.url
        )

        credentials = flow.credentials

    except Exception:
        return redirect(
            "/?auth_error=token_exchange_failed"
        )

    try:

        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

    except Exception:
        return redirect(
            "/?auth_error=invalid_token"
        )

    google_id = id_info.get("sub")
    email = id_info.get("email")

    if not email:
        return redirect(
            "/?auth_error=no_email"
        )

    name = (
        id_info.get("name")
        or email.split("@")[0]
    )

    user = User.objects(
        email=email
    ).first()

    if not user:

        user = User(
            name=name,
            email=email,
            role="attendee",
            google_id=google_id,
        )

        user.password_hash = (
            "oauth-no-password"
        )

        if id_info.get("picture"):
            user.avatar_url = id_info["picture"]

        user.save()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "name": user.name
        }
    )

    frontend_url = os.environ.get(
        "FRONTEND_URL",
        "http://localhost:3000"
    )

    return redirect(
        f"{frontend_url}"
        f"/?sc_token={access_token}"
        f"&user_id={user.id}"
    )