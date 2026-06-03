"""
SkillConnect – Live Event WebRTC & Streaming Routes
======================================================
Advanced live streaming and WebRTC signaling system with:
- WebRTC signaling
- Broadcaster/viewer architecture
- Live room management
- Viewer analytics
- Live chat
- Raise hand feature
- Viewer count tracking
- ICE server configuration
- Live stream controls
"""

from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required
)

from flask_socketio import (
    join_room,
    leave_room
)

from datetime import (
    datetime,
    timezone
)

import requests
import os

from app.models.event_model import Event

from app.utils.jwt_utils import (
    get_current_user,
    get_object_or_404
)

from app.utils.decorators import (
    role_required
)

live_bp = Blueprint(
    "live",
    __name__
)


# ═════════════════════════════════════════════════════════════
# IN-MEMORY LIVE STORE
# ═════════════════════════════════════════════════════════════

_room_broadcasters = {}

_room_viewers = {}

_room_live = {}

_room_chat_history = {}

_room_started_at = {}


# ═════════════════════════════════════════════════════════════
# ICE SERVERS
# ═════════════════════════════════════════════════════════════

@live_bp.route(
    "/ice-servers",
    methods=["GET"]
)
def get_ice_servers():
    """
    Get ICE server configuration
    ---
    tags:
      - Live Streaming
    """

    metered_key = os.getenv(
        "METERED_API_KEY",
        ""
    )

    if (
        metered_key
        and metered_key
        != "your-metered-api-key-here"
    ):

        try:

            response = requests.get(

                "https://skillconnect.metered.live/api/v1/turn/credentials",

                params={
                    "apiKey":
                        metered_key
                },

                timeout=5,
            )

            if response.ok:

                return jsonify({
                    "iceServers":
                        response.json()
                }), 200

        except Exception:
            pass

    # Free TURN servers fallback

    ice_servers = [

        {
            "urls":
                "stun:stun.l.google.com:19302"
        },

        {
            "urls":
                "stun:stun1.l.google.com:19302"
        },

        {
            "urls":
                "turn:openrelay.metered.ca:80",

            "username":
                "openrelayproject",

            "credential":
                "openrelayproject",
        },

        {
            "urls":
                "turn:openrelay.metered.ca:443",

            "username":
                "openrelayproject",

            "credential":
                "openrelayproject",
        },

    ]

    return jsonify({
        "iceServers":
            ice_servers
    }), 200


# ═════════════════════════════════════════════════════════════
# LIVE STATUS
# ═════════════════════════════════════════════════════════════

@live_bp.route(
    "/<event_id>/status",
    methods=["GET"]
)
def live_status(event_id):
    """
    Get live status
    ---
    tags:
      - Live Streaming
    """

    return jsonify({

        "event_id":
            event_id,

        "is_live":
            _room_live.get(
                event_id,
                False
            ),

        "viewer_count":
            len(
                _room_viewers.get(
                    event_id,
                    set()
                )
            ),

        "broadcaster_connected":
            event_id
            in _room_broadcasters,

        "started_at":
            _room_started_at.get(
                event_id
            )

    }), 200


# ═════════════════════════════════════════════════════════════
# START LIVE STREAM
# ═════════════════════════════════════════════════════════════

@live_bp.route(
    "/<event_id>/start",
    methods=["POST"]
)
@jwt_required()
@role_required("organizer", "admin")
def start_live(event_id):
    """
    Start live stream
    ---
    tags:
      - Live Streaming
    security:
      - Bearer: []
    """

    user = get_current_user()

    event = get_object_or_404(

        Event,

        id=event_id,

        description=
            "Event not found"

    )

    if (

        user.role != "admin"

        and

        str(event.created_by.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "Not your event"
        }), 403

    event.is_live = True

    event.live_started_at = datetime.now(
        timezone.utc
    )

    event.save()

    _room_live[event_id] = True

    _room_started_at[event_id] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    return jsonify({

        "message":
            "Live stream started",

        "event_id":
            event_id,

        "started_at":
            _room_started_at[event_id]

    }), 200


# ═════════════════════════════════════════════════════════════
# STOP LIVE STREAM
# ═════════════════════════════════════════════════════════════

@live_bp.route(
    "/<event_id>/stop",
    methods=["POST"]
)
@jwt_required()
@role_required("organizer", "admin")
def stop_live(event_id):
    """
    Stop live stream
    ---
    tags:
      - Live Streaming
    security:
      - Bearer: []
    """

    user = get_current_user()

    event = get_object_or_404(

        Event,

        id=event_id,

        description=
            "Event not found"

    )

    if (

        user.role != "admin"

        and

        str(event.created_by.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "Not your event"
        }), 403

    event.is_live = False

    event.live_ended_at = datetime.now(
        timezone.utc
    )

    event.save()

    _room_live[event_id] = False

    _room_broadcasters.pop(
        event_id,
        None
    )

    _room_viewers.pop(
        event_id,
        None
    )

    return jsonify({

        "message":
            "Live stream ended",

        "event_id":
            event_id

    }), 200


# ═════════════════════════════════════════════════════════════
# LIVE ANALYTICS
# ═════════════════════════════════════════════════════════════

@live_bp.route(
    "/<event_id>/analytics",
    methods=["GET"]
)
@jwt_required()
@role_required("organizer", "admin")
def live_analytics(event_id):
    """
    Live analytics
    ---
    tags:
      - Live Analytics
    security:
      - Bearer: []
    """

    viewers = list(
        _room_viewers.get(
            event_id,
            set()
        )
    )

    return jsonify({

        "event_id":
            event_id,

        "is_live":
            _room_live.get(
                event_id,
                False
            ),

        "viewer_count":
            len(viewers),

        "active_viewers":
            viewers,

        "chat_messages":
            len(
                _room_chat_history.get(
                    event_id,
                    []
                )
            ),

    }), 200


# ═════════════════════════════════════════════════════════════
# CHAT HISTORY
# ═════════════════════════════════════════════════════════════

@live_bp.route(
    "/<event_id>/chat-history",
    methods=["GET"]
)
@jwt_required()
def chat_history(event_id):
    """
    Get live chat history
    ---
    tags:
      - Live Chat
    security:
      - Bearer: []
    """

    return jsonify({

        "event_id":
            event_id,

        "messages":
            _room_chat_history.get(
                event_id,
                []
            )

    }), 200


# ═════════════════════════════════════════════════════════════
# SOCKET.IO EVENTS
# ═════════════════════════════════════════════════════════════

def register_socketio_events(socketio):
    """
    Register Socket.IO events
    """

    # ─────────────────────────────────────────
    # CONNECT
    # ─────────────────────────────────────────

    @socketio.on("connect")
    def on_connect():
        pass


    # ─────────────────────────────────────────
    # DISCONNECT
    # ─────────────────────────────────────────

    @socketio.on("disconnect")
    def on_disconnect():

        sid = request.sid

        for event_id, broadcaster_sid in list(
            _room_broadcasters.items()
        ):

            if broadcaster_sid == sid:

                del _room_broadcasters[event_id]

                _room_live[event_id] = False

                socketio.emit(

                    "broadcaster-disconnected",

                    room=f"live:{event_id}"

                )

        for event_id, viewers in list(
            _room_viewers.items()
        ):

            if sid in viewers:

                viewers.discard(sid)

                broadcaster_sid = (
                    _room_broadcasters.get(
                        event_id
                    )
                )

                if broadcaster_sid:

                    socketio.emit(

                        "viewer-disconnected",

                        {
                            "viewer_id": sid
                        },

                        room=broadcaster_sid

                    )


    # ─────────────────────────────────────────
    # BROADCASTER READY
    # ─────────────────────────────────────────

    @socketio.on("broadcaster-ready")
    def on_broadcaster_ready(data):

        sid = request.sid

        event_id = data.get(
            "event_id",
            ""
        )

        room = f"live:{event_id}"

        _room_broadcasters[event_id] = sid

        _room_live[event_id] = True

        join_room(room)

        viewers = _room_viewers.get(
            event_id,
            set()
        )

        for viewer_sid in viewers:

            socketio.emit(

                "broadcaster-joined",

                {
                    "broadcaster_id":
                        sid
                },

                room=viewer_sid

            )


    # ─────────────────────────────────────────
    # VIEWER JOIN
    # ─────────────────────────────────────────

    @socketio.on("viewer-join")
    def on_viewer_join(data):

        sid = request.sid

        event_id = data.get(
            "event_id",
            ""
        )

        room = f"live:{event_id}"

        join_room(room)

        _room_viewers.setdefault(
            event_id,
            set()
        ).add(sid)

        broadcaster_sid = (
            _room_broadcasters.get(
                event_id
            )
        )

        if broadcaster_sid:

            socketio.emit(

                "viewer-joined",

                {
                    "viewer_id":
                        sid
                },

                room=broadcaster_sid

            )

            socketio.emit(

                "broadcaster-joined",

                {
                    "broadcaster_id":
                        broadcaster_sid
                },

                room=sid

            )

        else:

            socketio.emit(
                "waiting-for-broadcaster",
                room=sid
            )


    # ─────────────────────────────────────────
    # OFFER
    # ─────────────────────────────────────────

    @socketio.on("offer")
    def on_offer(data):

        target = data.get("target")

        if target:

            socketio.emit(

                "offer",

                {
                    "sdp":
                        data.get("sdp"),

                    "sender":
                        request.sid,
                },

                room=target

            )


    # ─────────────────────────────────────────
    # ANSWER
    # ─────────────────────────────────────────

    @socketio.on("answer")
    def on_answer(data):

        target = data.get("target")

        if target:

            socketio.emit(

                "answer",

                {
                    "sdp":
                        data.get("sdp"),

                    "sender":
                        request.sid,
                },

                room=target

            )


    # ─────────────────────────────────────────
    # ICE CANDIDATE
    # ─────────────────────────────────────────

    @socketio.on("ice-candidate")
    def on_ice_candidate(data):

        target = data.get("target")

        if target:

            socketio.emit(

                "ice-candidate",

                {
                    "candidate":
                        data.get(
                            "candidate"
                        ),

                    "sender":
                        request.sid,
                },

                room=target

            )


    # ─────────────────────────────────────────
    # LIVE CHAT
    # ─────────────────────────────────────────

    @socketio.on("live-chat")
    def on_live_chat(data):

        event_id = data.get(
            "event_id",
            ""
        )

        room = f"live:{event_id}"

        message_data = {

            "name":
                data.get(
                    "name",
                    "Anonymous"
                ),

            "message":
                data.get(
                    "message",
                    ""
                ),

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat()

        }

        _room_chat_history.setdefault(
            event_id,
            []
        ).append(message_data)

        socketio.emit(
            "live-chat",
            message_data,
            room=room
        )


    # ─────────────────────────────────────────
    # RAISE HAND
    # ─────────────────────────────────────────

    @socketio.on("viewer-raise-hand")
    def on_raise_hand(data):

        event_id = data.get(
            "event_id",
            ""
        )

        broadcaster_sid = (
            _room_broadcasters.get(
                event_id
            )
        )

        if broadcaster_sid:

            socketio.emit(

                "viewer-raise-hand",

                {
                    "viewer_id":
                        request.sid,

                    "name":
                        data.get(
                            "name",
                            "Viewer"
                        ),
                },

                room=broadcaster_sid

            )


    # ─────────────────────────────────────────
    # VIEWER COUNT
    # ─────────────────────────────────────────

    @socketio.on("request-viewer-count")
    def on_viewer_count(data):

        event_id = data.get(
            "event_id",
            ""
        )

        count = len(
            _room_viewers.get(
                event_id,
                set()
            )
        )

        room = f"live:{event_id}"

        socketio.emit(

            "viewer-count",

            {
                "count": count
            },

            room=room

        )