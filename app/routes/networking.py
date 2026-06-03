"""
SkillConnect – Networking Routes
===================================
Advanced networking and connection management system with:
- Connection requests
- Accept/reject requests
- User networking
- Event networking
- Mutual connections
- Networking analytics
- Search users
- Connection suggestions
"""

from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required
)

from datetime import (
    datetime,
    timezone
)

from app.models.networking_model import NetworkingRequest
from app.models.user_model import User
from app.models.event_model import Event

from app.utils.jwt_utils import (
    get_current_user,
    get_object_or_404
)

networking_bp = Blueprint(
    "networking",
    __name__
)


# ═════════════════════════════════════════════════════════════
# SEND NETWORK REQUEST
# ═════════════════════════════════════════════════════════════

@networking_bp.route(
    "/request",
    methods=["POST"]
)
@jwt_required()
def send_request():
    """
    Send networking request
    ---
    tags:
      - Networking
    security:
      - Bearer: []
    """

    data = request.get_json()

    receiver_id = data.get(
        "receiver_id"
    )

    if not receiver_id:

        return jsonify({
            "error":
                "receiver_id is required"
        }), 400

    user = get_current_user()

    if str(user.id) == str(receiver_id):

        return jsonify({
            "error":
                "Cannot send request to yourself"
        }), 400

    receiver = User.objects(
        id=receiver_id
    ).first()

    if not receiver:

        return jsonify({
            "error":
                "Receiver not found"
        }), 404

    if not receiver.is_active:

        return jsonify({
            "error":
                "Receiver account inactive"
        }), 400

    event = None

    if data.get("event_id"):

        event = Event.objects(
            id=data["event_id"]
        ).first()

    existing_request = NetworkingRequest.objects(

        sender=user,

        receiver=receiver,

        event=event

    ).first()

    if existing_request:

        return jsonify({

            "error":
                "Request already exists",

            "status":
                existing_request.status

        }), 409

    reverse_request = NetworkingRequest.objects(

        sender=receiver,

        receiver=user,

        status="pending"

    ).first()

    # Auto accept if reverse request exists

    if reverse_request:

        reverse_request.status = "accepted"

        reverse_request.responded_at = (
            datetime.now(
                timezone.utc
            )
        )

        reverse_request.save()

        return jsonify({

            "message":
                "Connection automatically accepted",

            "request":
                reverse_request.to_dict()

        }), 200

    networking_request = NetworkingRequest(

        sender=user,

        receiver=receiver,

        event=event,

        message=data.get(
            "message",
            ""
        ).strip() or None,

        created_at=datetime.now(
            timezone.utc
        )

    )

    networking_request.save()

    return jsonify({

        "message":
            "Networking request sent",

        "request":
            networking_request.to_dict()

    }), 201


# ═════════════════════════════════════════════════════════════
# ACCEPT REQUEST
# ═════════════════════════════════════════════════════════════

@networking_bp.route(
    "/accept",
    methods=["POST"]
)
@jwt_required()
def accept_request():
    """
    Accept networking request
    ---
    tags:
      - Networking
    security:
      - Bearer: []
    """

    data = request.get_json()

    request_id = data.get(
        "request_id"
    )

    if not request_id:

        return jsonify({
            "error":
                "request_id is required"
        }), 400

    networking_request = get_object_or_404(

        NetworkingRequest,

        id=request_id,

        description=
            "Request not found"

    )

    user = get_current_user()

    if (
        str(networking_request.receiver.id)
        != str(user.id)
    ):

        return jsonify({
            "error":
                "Unauthorized"
        }), 403

    if networking_request.status != "pending":

        return jsonify({
            "error":
                f"Request already "
                f"{networking_request.status}"
        }), 400

    networking_request.status = "accepted"

    networking_request.responded_at = (
        datetime.now(
            timezone.utc
        )
    )

    networking_request.save()

    return jsonify({

        "message":
            "Request accepted",

        "request":
            networking_request.to_dict()

    }), 200


# ═════════════════════════════════════════════════════════════
# RESPOND TO REQUEST
# ═════════════════════════════════════════════════════════════

@networking_bp.route(
    "/request/<request_id>",
    methods=["PUT"]
)
@jwt_required()
def respond_request(request_id):
    """
    Accept or reject request
    ---
    tags:
      - Networking
    security:
      - Bearer: []
    """

    networking_request = get_object_or_404(

        NetworkingRequest,

        id=request_id,

        description=
            "Request not found"

    )

    user = get_current_user()

    if (
        str(networking_request.receiver.id)
        != str(user.id)
    ):

        return jsonify({
            "error":
                "Unauthorized"
        }), 403

    if networking_request.status != "pending":

        return jsonify({
            "error":
                f"Request already "
                f"{networking_request.status}"
        }), 400

    data = request.get_json()

    action = data.get(
        "action",
        ""
    ).lower()

    if action not in (
        "accept",
        "reject"
    ):

        return jsonify({
            "error":
                "action must be "
                "'accept' or 'reject'"
        }), 400

    networking_request.status = (
        "accepted"
        if action == "accept"
        else "rejected"
    )

    networking_request.responded_at = (
        datetime.now(
            timezone.utc
        )
    )

    networking_request.save()

    return jsonify({

        "message":
            f"Request "
            f"{networking_request.status}",

        "request":
            networking_request.to_dict()

    }), 200


# ═════════════════════════════════════════════════════════════
# MY CONNECTIONS
# ═════════════════════════════════════════════════════════════

@networking_bp.route(
    "/connections",
    methods=["GET"]
)
@jwt_required()
def my_connections():
    """
    Get all user connections
    ---
    tags:
      - Networking
    security:
      - Bearer: []
    """

    user = get_current_user()

    sent_connections = NetworkingRequest.objects(

        sender=user,

        status="accepted"

    )

    received_connections = NetworkingRequest.objects(

        receiver=user,

        status="accepted"

    )

    connections = []

    seen_users = set()

    for request_obj in sent_connections:

        connection_user = request_obj.receiver

        user_id = str(
            connection_user.id
        )

        if user_id not in seen_users:

            seen_users.add(user_id)

            connections.append({

                "connection":
                    connection_user.to_dict(),

                "connected_at":
                    (
                        request_obj.responded_at.isoformat()
                        if request_obj.responded_at
                        else None
                    ),

                "event_id":
                    (
                        str(request_obj.event.id)
                        if request_obj.event
                        else None
                    )

            })

    for request_obj in received_connections:

        connection_user = request_obj.sender

        user_id = str(
            connection_user.id
        )

        if user_id not in seen_users:

            seen_users.add(user_id)

            connections.append({

                "connection":
                    connection_user.to_dict(),

                "connected_at":
                    (
                        request_obj.responded_at.isoformat()
                        if request_obj.responded_at
                        else None
                    ),

                "event_id":
                    (
                        str(request_obj.event.id)
                        if request_obj.event
                        else None
                    )

            })

    return jsonify({

        "total_connections":
            len(connections),

        "connections":
            connections

    }), 200


# ═════════════════════════════════════════════════════════════
# RECEIVED REQUESTS
# ═════════════════════════════════════════════════════════════

@networking_bp.route(
    "/my-requests",
    methods=["GET"]
)
@jwt_required()
def received_requests():
    """
    Get received requests
    ---
    tags:
      - Networking
    security:
      - Bearer: []
    """

    user = get_current_user()

    query = NetworkingRequest.objects(
        receiver=user
    )

    status = request.args.get(
        "status"
    )

    if status:

        query = query.filter(
            status=status
        )

    requests_list = query.order_by(
        "-created_at"
    )

    return jsonify({

        "total":
            requests_list.count(),

        "requests": [
            request_obj.to_dict()
            for request_obj in requests_list
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# SENT REQUESTS
# ═════════════════════════════════════════════════════════════

@networking_bp.route(
    "/sent-requests",
    methods=["GET"]
)
@jwt_required()
def sent_requests():
    """
    Get sent requests
    ---
    tags:
      - Networking
    security:
      - Bearer: []
    """

    user = get_current_user()

    query = NetworkingRequest.objects(
        sender=user
    )

    status = request.args.get(
        "status"
    )

    if status:

        query = query.filter(
            status=status
        )

    requests_list = query.order_by(
        "-created_at"
    )

    return jsonify({

        "total":
            requests_list.count(),

        "sent_requests": [
            request_obj.to_dict()
            for request_obj in requests_list
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# DELETE REQUEST
# ═════════════════════════════════════════════════════════════

@networking_bp.route(
    "/request/<request_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_request(request_id):
    """
    Delete networking request
    ---
    tags:
      - Networking
    security:
      - Bearer: []
    """

    networking_request = get_object_or_404(

        NetworkingRequest,

        id=request_id,

        description=
            "Request not found"

    )

    user = get_current_user()

    if (

        str(networking_request.sender.id)
        != str(user.id)

        and

        user.role != "admin"

    ):

        return jsonify({
            "error":
                "Unauthorized"
        }), 403

    networking_request.delete()

    return jsonify({
        "message":
            "Request deleted successfully"
    }), 200


# ═════════════════════════════════════════════════════════════
# USER SEARCH
# ═════════════════════════════════════════════════════════════

@networking_bp.route(
    "/search-users",
    methods=["GET"]
)
@jwt_required()
def search_users():
    """
    Search networking users
    ---
    tags:
      - Networking
    security:
      - Bearer: []
    """

    search = request.args.get(
        "search",
        ""
    ).strip()

    if not search:

        return jsonify({
            "users": []
        }), 200

    users = User.objects(

        __raw__={

            "$or": [

                {
                    "name": {
                        "$regex": search,
                        "$options": "i"
                    }
                },

                {
                    "email": {
                        "$regex": search,
                        "$options": "i"
                    }
                }

            ]
        }

    )[:20]

    return jsonify({

        "total":
            len(users),

        "users": [
            user.to_dict()
            for user in users
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# NETWORK ANALYTICS
# ═════════════════════════════════════════════════════════════

@networking_bp.route(
    "/analytics/overview",
    methods=["GET"]
)
@jwt_required()
def networking_analytics():
    """
    Networking analytics
    ---
    tags:
      - Networking Analytics
    security:
      - Bearer: []
    """

    total_requests = (
        NetworkingRequest.objects.count()
    )

    accepted_requests = (
        NetworkingRequest.objects(
            status="accepted"
        ).count()
    )

    pending_requests = (
        NetworkingRequest.objects(
            status="pending"
        ).count()
    )

    rejected_requests = (
        NetworkingRequest.objects(
            status="rejected"
        ).count()
    )

    return jsonify({

        "total_requests":
            total_requests,

        "accepted_requests":
            accepted_requests,

        "pending_requests":
            pending_requests,

        "rejected_requests":
            rejected_requests,

        "acceptance_rate":
            round(
                (
                    accepted_requests
                    / total_requests
                ) * 100,
                2
            ) if total_requests > 0 else 0

    }), 200