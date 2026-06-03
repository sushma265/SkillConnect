"""
SkillConnect – Live Event WebRTC Signaling
===========================================
Socket.IO event handlers that act as a WebRTC signaling server.

Architecture (1 broadcaster → N viewers):
  1. Organizer opens /live/<event_id>?role=broadcaster
  2. Viewers open /live/<event_id>?role=viewer
  3. This server relays SDP offers, answers, and ICE candidates
     between broadcaster and each viewer.

Socket.IO rooms:
  Every event gets its own room  →  "live:<event_id>"
  The broadcaster's socket ID is stored in memory per room.

REST endpoints:
  GET  /live/<event_id>/status  – Check if a room is currently live
  POST /live/<event_id>/start   – Mark event as live (JWT required, organizer)
  POST /live/<event_id>/stop    – Mark event as not live (JWT required, organizer)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, decode_token
from flask_socketio import join_room, leave_room, emit
import os

from app.models.event_model import Event
from app.utils.jwt_utils import get_current_user, get_object_or_404
from app.utils.decorators import role_required

live_bp = Blueprint("live", __name__)

# In-memory store: event_id → broadcaster socket_id
# (For multi-process deployments use Redis; fine for single-process)
_room_broadcasters: dict[str, str] = {}   # event_id -> sid
_room_viewers: dict[str, set] = {}         # event_id -> {sid, ...}
_room_live: dict[str, bool] = {}           # event_id -> is_live


# ── REST – Return ICE server config (STUN + TURN) ──────────────────────
@live_bp.route("/ice-servers", methods=["GET"])
def get_ice_servers():
    """
    Returns ICE server configuration for WebRTC.
    TURN credentials are kept server-side and never exposed in frontend JS.

    Priority:
      1. Metered.ca API  – if METERED_API_KEY is set (best reliability)
      2. Open Relay Project – free public TURN, no account needed (fallback)
    """
    import requests as req_lib

    metered_key = os.getenv("METERED_API_KEY", "")

    if metered_key and metered_key != "your-metered-api-key-here":
        try:
            # Fetch temporary TURN credentials from Metered API
            r = req_lib.get(
                "https://skillconnect.metered.live/api/v1/turn/credentials",
                params={"apiKey": metered_key},
                timeout=5,
            )
            if r.ok:
                return jsonify({"iceServers": r.json()}), 200
        except Exception:
            pass  # fall through to default

    # Free Open Relay Project TURN servers (no account needed, works in production)
    ice_servers = [
        {"urls": "stun:stun.l.google.com:19302"},
        {"urls": "stun:stun1.l.google.com:19302"},
        {
            "urls": "turn:openrelay.metered.ca:80",
            "username": "openrelayproject",
            "credential": "openrelayproject",
        },
        {
            "urls": "turn:openrelay.metered.ca:443",
            "username": "openrelayproject",
            "credential": "openrelayproject",
        },
        {
            "urls": "turn:openrelay.metered.ca:443?transport=tcp",
            "username": "openrelayproject",
            "credential": "openrelayproject",
        },
        {
            "urls": "turn:openrelay.metered.ca:80?transport=tcp",
            "username": "openrelayproject",
            "credential": "openrelayproject",
        },
    ]
    return jsonify({"iceServers": ice_servers}), 200


# ── REST – Check live status ────────────────────────────────────────────
@live_bp.route("/<event_id>/status", methods=["GET"])
def live_status(event_id):
    """Return whether an event room is currently live."""
    return jsonify({
        "event_id": event_id,
        "is_live": _room_live.get(event_id, False),
        "viewer_count": len(_room_viewers.get(event_id, set())),
    }), 200


# ── REST – Organizer starts live ────────────────────────────────────────
@live_bp.route("/<event_id>/start", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def start_live(event_id):
    user = get_current_user()
    ev = get_object_or_404(Event, id=event_id, description="Event not found")
    if user.role != "admin" and str(ev.created_by.id) != str(user.id):
        return jsonify({"error": "Not your event"}), 403
    ev.is_live = True
    ev.save()
    _room_live[event_id] = True
    return jsonify({"message": "Event is now live", "event_id": event_id}), 200


# ── REST – Organizer stops live ─────────────────────────────────────────
@live_bp.route("/<event_id>/stop", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def stop_live(event_id):
    user = get_current_user()
    ev = get_object_or_404(Event, id=event_id, description="Event not found")
    if user.role != "admin" and str(ev.created_by.id) != str(user.id):
        return jsonify({"error": "Not your event"}), 403
    ev.is_live = False
    ev.save()
    _room_live[event_id] = False
    _room_broadcasters.pop(event_id, None)
    return jsonify({"message": "Live stream ended"}), 200


# ── Socket.IO event registration ────────────────────────────────────────
def register_socketio_events(sio):
    """Attach all WebRTC signaling Socket.IO event handlers to `sio`."""

    @sio.on("connect")
    def on_connect():
        pass  # no-op; handshake handled per room join

    @sio.on("disconnect")
    def on_disconnect():
        sid = request.sid
        # Clean up from all rooms this socket was in
        for event_id, bsid in list(_room_broadcasters.items()):
            if bsid == sid:
                del _room_broadcasters[event_id]
                _room_live[event_id] = False
                # Notify all viewers that the stream ended
                sio.emit("broadcaster-disconnected", room=f"live:{event_id}")

        for event_id, viewers in list(_room_viewers.items()):
            if sid in viewers:
                viewers.discard(sid)
                # Notify broadcaster that this viewer left
                bsid = _room_broadcasters.get(event_id)
                if bsid:
                    sio.emit("viewer-disconnected", {"viewer_id": sid}, room=bsid)

    # ── Broadcaster announces themselves ─────────────────────────────────
    @sio.on("broadcaster-ready")
    def on_broadcaster_ready(data):
        """
        Organizer's browser sends this after getUserMedia succeeds.
        data: { event_id: str }
        """
        sid = request.sid
        event_id = data.get("event_id", "")
        room = f"live:{event_id}"

        _room_broadcasters[event_id] = sid
        _room_live[event_id] = True
        join_room(room)

        # Tell any already-waiting viewers a broadcaster is here
        viewers = _room_viewers.get(event_id, set())
        for vsid in list(viewers):
            sio.emit("broadcaster-joined", {"broadcaster_id": sid}, room=vsid)

    # ── Viewer joins a live room ──────────────────────────────────────────
    @sio.on("viewer-join")
    def on_viewer_join(data):
        """
        Viewer's browser sends this when they open the live page.
        data: { event_id: str }
        """
        sid = request.sid
        event_id = data.get("event_id", "")
        room = f"live:{event_id}"

        join_room(room)
        _room_viewers.setdefault(event_id, set()).add(sid)

        bsid = _room_broadcasters.get(event_id)
        if bsid:
            # Tell the broadcaster a new viewer arrived
            sio.emit("viewer-joined", {"viewer_id": sid}, room=bsid)
            # Tell the viewer that the broadcaster is already live
            sio.emit("broadcaster-joined", {"broadcaster_id": bsid}, room=sid)
        else:
            # No broadcaster yet – tell viewer to wait
            sio.emit("waiting-for-broadcaster", room=sid)

    # ── SDP Offer: Broadcaster → specific Viewer ─────────────────────────
    @sio.on("offer")
    def on_offer(data):
        """
        data: { target: viewer_sid, sdp: {...} }
        Relayed only to the target viewer.
        """
        target = data.get("target")
        if target:
            sio.emit("offer", {
                "sdp": data.get("sdp"),
                "sender": request.sid,
            }, room=target)

    # ── SDP Answer: Viewer → Broadcaster ─────────────────────────────────
    @sio.on("answer")
    def on_answer(data):
        """
        data: { target: broadcaster_sid, sdp: {...} }
        """
        target = data.get("target")
        if target:
            sio.emit("answer", {
                "sdp": data.get("sdp"),
                "sender": request.sid,
            }, room=target)

    # ── ICE Candidate relay ──────────────────────────────────────────────
    @sio.on("ice-candidate")
    def on_ice_candidate(data):
        """
        data: { target: sid, candidate: {...} }
        """
        target = data.get("target")
        if target:
            sio.emit("ice-candidate", {
                "candidate": data.get("candidate"),
                "sender": request.sid,
            }, room=target)

    # ── Chat message in live room ────────────────────────────────────────
    @sio.on("live-chat")
    def on_live_chat(data):
        """
        data: { event_id: str, name: str, message: str }
        Broadcast chat message to all users in the room.
        """
        event_id = data.get("event_id", "")
        room = f"live:{event_id}"
        sio.emit("live-chat", {
            "name": data.get("name", "Anonymous"),
            "message": data.get("message", ""),
            "ts": data.get("ts", ""),
        }, room=room)

    # ── Broadcaster hand-raise toggle ────────────────────────────────────
    @sio.on("viewer-raise-hand")
    def on_raise_hand(data):
        event_id = data.get("event_id", "")
        bsid = _room_broadcasters.get(event_id)
        if bsid:
            sio.emit("viewer-raise-hand", {
                "viewer_id": request.sid,
                "name": data.get("name", "Viewer"),
            }, room=bsid)

    # ── Viewer count broadcast ────────────────────────────────────────────
    @sio.on("request-viewer-count")
    def on_viewer_count(data):
        event_id = data.get("event_id", "")
        count = len(_room_viewers.get(event_id, set()))
        room = f"live:{event_id}"
        sio.emit("viewer-count", {"count": count}, room=room)
