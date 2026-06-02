"""
SkillConnect – Networking Routes
===================================
Manages peer-to-peer networking requests and connections.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timezone

from app.models.networking_model import NetworkingRequest
from app.models.user_model import User
from app.models.event_model import Event
from app.utils.jwt_utils import get_current_user, get_object_or_404

networking_bp = Blueprint("networking", __name__)


# ── POST /network/request ──────────────────────────────────────────────
@networking_bp.route("/request", methods=["POST"])
@jwt_required()
def send_request():
    """
    Send a networking / connection request to another user.
    ---
    tags: [Networking]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [receiver_id]
          properties:
            receiver_id: {type: string}
            event_id:    {type: string}
            message:     {type: string}
    responses:
      201: {description: Request sent}
      409: {description: Request already sent}
    """
    data = request.get_json()
    receiver_id = data.get("receiver_id")

    if not receiver_id:
        return jsonify({"error": "receiver_id is required"}), 400

    user = get_current_user()
    if str(user.id) == str(receiver_id):
        return jsonify({
            "error": "Cannot send request to yourself"
        }), 400

    receiver = User.objects(id=receiver_id).first()
    if not receiver:
        return jsonify({"error": "Receiver not found"}), 404

    if not receiver.is_active:
        return jsonify({
            "error": "Receiver account is not active"
        }), 400

    # Optional event context
    event = None
    if data.get("event_id"):
        event = Event.objects(id=data["event_id"]).first()

    # Check for existing request
    existing = NetworkingRequest.objects(
        sender=user, receiver=receiver, event=event
    ).first()
    if existing:
        return jsonify({
            "error": "Request already sent",
            "status": existing.status,
        }), 409

    req = NetworkingRequest(
        sender=user,
        receiver=receiver,
        event=event,
        message=data.get("message", "").strip() or None,
    )
    req.save()

    return jsonify({
        "message": "Networking request sent",
        "request": req.to_dict(),
    }), 201


# ── POST /network/accept ───────────────────────────────────────────────
@networking_bp.route("/accept", methods=["POST"])
@jwt_required()
def accept_request():
    """
    Accept a networking request by its ID.
    ---
    tags: [Networking]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [request_id]
          properties:
            request_id: {type: string}
    responses:
      200: {description: Request accepted}
    """
    data = request.get_json()
    req_id = data.get("request_id")

    if not req_id:
        return jsonify({"error": "request_id is required"}), 400

    req = get_object_or_404(
        NetworkingRequest, id=req_id,
        description="Request not found",
    )
    user = get_current_user()

    if str(req.receiver.id) != str(user.id):
        return jsonify({
            "error": "You can only respond to requests sent to you"
        }), 403

    if req.status != "pending":
        return jsonify({
            "error": f"Request already {req.status}"
        }), 400

    req.status = "accepted"
    req.responded_at = datetime.now(timezone.utc)
    req.save()

    return jsonify({
        "message": "Request accepted",
        "request": req.to_dict(),
    }), 200


# ── PUT /network/request/<id> ──────────────────────────────────────────
@networking_bp.route("/request/<req_id>", methods=["PUT"])
@jwt_required()
def respond_to_request(req_id):
    """
    Accept or reject a networking request.
    ---
    tags: [Networking]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [action]
          properties:
            action: {type: string, enum: [accept, reject]}
    responses:
      200: {description: Request updated}
    """
    req = get_object_or_404(
        NetworkingRequest, id=req_id,
        description="Request not found",
    )
    user = get_current_user()

    if str(req.receiver.id) != str(user.id):
        return jsonify({
            "error": "You can only respond to requests sent to you"
        }), 403

    if req.status != "pending":
        return jsonify({
            "error": f"Request already {req.status}"
        }), 400

    data = request.get_json()
    action = data.get("action", "").lower()
    if action not in ("accept", "reject"):
        return jsonify({
            "error": "action must be 'accept' or 'reject'"
        }), 400

    req.status = "accepted" if action == "accept" else "rejected"
    req.responded_at = datetime.now(timezone.utc)
    req.save()

    return jsonify({
        "message": f"Request {req.status}",
        "request": req.to_dict(),
    }), 200


# ── GET /network/connections ────────────────────────────────────────────
@networking_bp.route("/connections", methods=["GET"])
@jwt_required()
def my_connections():
    """
    Get all accepted connections for the current user.
    ---
    tags: [Networking]
    security: [{Bearer: []}]
    responses:
      200: {description: List of connections}
    """
    user = get_current_user()

    sent = NetworkingRequest.objects(
        sender=user, status="accepted"
    )
    recv = NetworkingRequest.objects(
        receiver=user, status="accepted"
    )

    connections = []
    seen = set()

    for r in sent:
        uid = str(r.receiver.id)
        if uid not in seen:
            seen.add(uid)
            connections.append({
                "connection": r.receiver.to_dict(),
                "connected_at": (
                    r.responded_at.isoformat()
                    if r.responded_at
                    else None
                ),
                "event_id": (
                    str(r.event.id) if r.event else None
                ),
            })

    for r in recv:
        uid = str(r.sender.id)
        if uid not in seen:
            seen.add(uid)
            connections.append({
                "connection": r.sender.to_dict(),
                "connected_at": (
                    r.responded_at.isoformat()
                    if r.responded_at
                    else None
                ),
                "event_id": (
                    str(r.event.id) if r.event else None
                ),
            })

    return jsonify({
        "total_connections": len(connections),
        "connections": connections,
    }), 200


# ── GET /network/my-requests ───────────────────────────────────────────
@networking_bp.route("/my-requests", methods=["GET"])
@jwt_required()
def my_received_requests():
    """
    Get networking requests received by the current user.
    ---
    tags: [Networking]
    security: [{Bearer: []}]
    """
    user = get_current_user()
    qs = NetworkingRequest.objects(receiver=user)
    if request.args.get("status"):
        qs = qs.filter(status=request.args["status"])
    return jsonify({
        "requests": [
            r.to_dict() for r in qs.order_by("-created_at")
        ]
    }), 200


# ── GET /network/sent-requests ─────────────────────────────────────────
@networking_bp.route("/sent-requests", methods=["GET"])
@jwt_required()
def my_sent_requests():
    """
    Get networking requests sent by the current user.
    ---
    tags: [Networking]
    security: [{Bearer: []}]
    """
    user = get_current_user()
    qs = NetworkingRequest.objects(sender=user)
    if request.args.get("status"):
        qs = qs.filter(status=request.args["status"])
    return jsonify({
        "sent_requests": [
            r.to_dict() for r in qs.order_by("-created_at")
        ]
    }), 200


# ── DELETE /network/request/<id> ───────────────────────────────────────
@networking_bp.route("/request/<req_id>", methods=["DELETE"])
@jwt_required()
def delete_request(req_id):
    """
    Withdraw a sent networking request.
    ---
    tags: [Networking]
    security: [{Bearer: []}]
    """
    req = get_object_or_404(
        NetworkingRequest, id=req_id,
        description="Request not found",
    )
    user = get_current_user()

    if (
        str(req.sender.id) != str(user.id)
        and user.role != "admin"
    ):
        return jsonify({
            "error": "You can only withdraw your own requests"
        }), 403

    req.delete()
    return jsonify({"message": "Request withdrawn"}), 200
