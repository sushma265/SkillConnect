from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)

from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


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
          required:
            - name
            - email
            - password

          properties:
            name:
              type: string
              example: John Doe

            email:
              type: string
              example: john@gmail.com

            password:
              type: string
              example: password123

            role:
              type: string
              example: user

    responses:
      201:
        description: Account created successfully

      400:
        description: Missing fields or invalid role

      409:
        description: Email already exists
    """

    data = request.get_json()

    required = ["name", "email", "password"]

    for field in required:
        if not data.get(field):
            return jsonify({
                "error": f"{field} is required"
            }), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({
            "error": "Email already registered"
        }), 409

    allowed_roles = ["user", "conductor"]

    role = data.get("role", "user")

    if role not in allowed_roles:
        return jsonify({
            "error": f"Role must be one of {allowed_roles}"
        }), 400

    user = User(
        name=data["name"],
        email=data["email"],
        role=role
    )

    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "Account created successfully",
        "user": user.to_dict()
    }), 201


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

          required:
            - email
            - password

          properties:
            email:
              type: string
              example: john@gmail.com

            password:
              type: string
              example: password123

    responses:
      200:
        description: Login successful

      400:
        description: Missing email or password

      401:
        description: Invalid credentials

      403:
        description: Account deactivated
    """

    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify({
            "error": "Email and password are required"
        }), 400

    user = User.query.filter_by(email=data["email"]).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    if not user.is_active:
        return jsonify({
            "error": "Account is deactivated. Contact admin."
        }), 403

    additional_claims = {
        "role": user.role,
        "name": user.name
    }

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": user.to_dict()
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Get Current User
    ---
    tags:
      - Authentication

    responses:
      200:
        description: Current logged in user

      401:
        description: Unauthorized

      404:
        description: User not found
    """

    user_id = get_jwt_identity()

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify({
        "user": user.to_dict()
    }), 200