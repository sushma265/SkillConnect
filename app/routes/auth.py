from flask import Blueprint, request, jsonify, redirect, url_for, session
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
import os

from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)

# ─── Google OAuth Config ──────────────────────────────────────────────────────
GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI  = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback")

# Scopes we request from Google
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email",
          "https://www.googleapis.com/auth/userinfo.profile"]


def make_flow():
    """Create a fresh OAuth flow object per request."""
    return Flow.from_client_config(
        {
            "web": {
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                "token_uri":     "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )


# ─── Existing Signup ───────────────────────────────────────────────────────────
@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    User Signup API
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, email, password]
          properties:
            name:     { type: string, example: John Doe }
            email:    { type: string, example: john@gmail.com }
            password: { type: string, example: password123 }
            role:     { type: string, example: user }
    responses:
      201: { description: Account created successfully }
      400: { description: Missing fields or invalid role }
      409: { description: Email already exists }
    """
    data = request.get_json()

    for field in ["name", "email", "password"]:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    role = data.get("role", "user")
    if role not in ["user", "conductor"]:
        return jsonify({"error": "Role must be one of ['user', 'conductor']"}), 400

    user = User(name=data["name"], email=data["email"], role=role)
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Account created successfully", "user": user.to_dict()}), 201


# ─── Existing Login ────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    User Login API
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email:    { type: string, example: john@gmail.com }
            password: { type: string, example: password123 }
    responses:
      200: { description: Login successful }
      400: { description: Missing email or password }
      401: { description: Invalid credentials }
      403: { description: Account deactivated }
    """
    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is deactivated. Contact admin."}), 403

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "name": user.name}
    )

    return jsonify({
        "message":      "Login successful",
        "access_token": access_token,
        "user":         user.to_dict()
    }), 200


# ─── Get Current User ──────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Get Current User
    ---
    tags:
      - Authentication
    responses:
      200: { description: Current logged in user }
      401: { description: Unauthorized }
      404: { description: User not found }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user.to_dict()}), 200


# ══════════════════════════════════════════════════════════════════════════════
#  GOOGLE OAUTH  —  Step 1: Redirect user to Google's consent screen
# ══════════════════════════════════════════════════════════════════════════════
@auth_bp.route("/google", methods=["GET"])
def google_login():
    """
    Initiate Google OAuth flow.
    Frontend calls: window.location.href = '/auth/google'
    ---
    tags:
      - Authentication
    responses:
      302: { description: Redirect to Google consent screen }
    """
    flow = make_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="select_account"          # always show account picker
    )
    session["oauth_state"] = state       # stored in Flask session to verify callback
    return redirect(auth_url)


# ══════════════════════════════════════════════════════════════════════════════
#  GOOGLE OAUTH  —  Step 2: Handle the callback from Google
# ══════════════════════════════════════════════════════════════════════════════
@auth_bp.route("/google/callback", methods=["GET"])
def google_callback():
    """
    Google OAuth callback — called by Google after user consents.
    Verifies the token, finds/creates the user, issues a JWT,
    then redirects the frontend to /?token=<jwt>
    ---
    tags:
      - Authentication
    responses:
      302: { description: Redirect to frontend with token or error }
    """
    # ── 1. Check for errors from Google ──────────────────────────────────────
    error = request.args.get("error")
    if error:
        return redirect(f"/?auth_error={error}")

    # ── 2. Verify state to prevent CSRF ──────────────────────────────────────
    state = request.args.get("state")
    if state != session.get("oauth_state"):
        return redirect("/?auth_error=state_mismatch")

    # ── 3. Exchange the code for tokens ──────────────────────────────────────
    try:
        flow = make_flow()
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
    except Exception as e:
        return redirect(f"/?auth_error=token_exchange_failed")

    # ── 4. Verify the ID token with Google's public keys ─────────────────────
    try:
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
    except ValueError:
        return redirect("/?auth_error=invalid_token")

    # ── 5. Extract user info from the verified token ──────────────────────────
    google_id = id_info.get("sub")       # unique Google user ID
    email     = id_info.get("email")
    name      = id_info.get("name") or email.split("@")[0]
    picture   = id_info.get("picture")   # optional — store if you want avatars

    if not email:
        return redirect("/?auth_error=no_email")

    # ── 6. Find existing user or create a new one ─────────────────────────────
    user = User.query.filter_by(email=email).first()

    if user:
        # Existing user: update Google ID if this is their first OAuth login
        if not getattr(user, "google_id", None):
            user.google_id = google_id
            db.session.commit()
    else:
        # Brand new user — create with role "user" (student) by default
        user = User(
            name=name,
            email=email,
            role="user",
            google_id=google_id,
            # No password for OAuth users; set_password not called
        )
        db.session.add(user)
        db.session.commit()

    # ── 7. Check if account is active ────────────────────────────────────────
    if not user.is_active:
        return redirect("/?auth_error=account_deactivated")

    # ── 8. Issue a JWT just like the normal login flow ────────────────────────
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "name": user.name}
    )

    # ── 9. Redirect frontend — token passed as query param ───────────────────
    #       The frontend JS reads this, stores it, and cleans the URL.
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5000")
    return redirect(f"{frontend_url}/?sc_token={access_token}&sc_user_id={user.id}")