"""
SkillConnect – Session Routes
================================
Advanced session management system with:
- Session CRUD
- Event schedule management
- Speaker details
- Live session support
- Session analytics
- Session filtering
- Timeline management
- Session status tracking
"""

from flask import (
    Blueprint,
    request,
    jsonify
)

from flask_jwt_extended import (
    jwt_required
)

from datetime import (
    datetime,
    timezone
)

from app.models.session_model import Session
from app.models.event_model import Event

from app.utils.decorators import (
    role_required
)

from app.utils.jwt_utils import (
    get_current_user,
    get_object_or_404
)

sessions_bp = Blueprint(
    "sessions",
    __name__
)

DATE_FMT = "%Y-%m-%d %H:%M"

SESSION_TYPES = (
    "keynote",
    "panel",
    "workshop",
    "networking",
    "break"
)


# ═════════════════════════════════════════════════════════════
# PARSE DATETIME
# ═════════════════════════════════════════════════════════════

def parse_datetime(value):
    """
    Parse datetime string
    """

    try:

        return datetime.strptime(
            value,
            DATE_FMT
        )

    except (
        ValueError,
        TypeError
    ):

        return None


# ═════════════════════════════════════════════════════════════
# CREATE SESSION
# ═════════════════════════════════════════════════════════════

@sessions_bp.route(
    "",
    methods=["POST"]
)
@jwt_required()
@role_required("organizer", "admin")
def create_session():
    """
    Create session
    ---
    tags:
      - Sessions
    security:
      - Bearer: []
    """

    data = request.get_json()

    required_fields = [

        "event_id",

        "title",

        "starts_at",

        "ends_at"

    ]

    for field in required_fields:

        if not data.get(field):

            return jsonify({
                "error":
                    f"{field} is required"
            }), 400

    event = get_object_or_404(

        Event,

        id=data["event_id"],

        description=
            "Event not found"

    )

    starts_at = parse_datetime(
        data["starts_at"]
    )

    ends_at = parse_datetime(
        data["ends_at"]
    )

    if not starts_at or not ends_at:

        return jsonify({
            "error":
                "starts_at and ends_at "
                "must be 'YYYY-MM-DD HH:MM'"
        }), 400

    if ends_at <= starts_at:

        return jsonify({
            "error":
                "ends_at must be after starts_at"
        }), 400

    session_type = data.get(
        "session_type",
        "keynote"
    )

    if session_type not in SESSION_TYPES:

        return jsonify({
            "error":
                f"session_type must be "
                f"one of {SESSION_TYPES}"
        }), 400

    user = get_current_user()

    session = Session(

        event=event,

        title=data["title"],

        description=data.get(
            "description"
        ),

        speaker_name=data.get(
            "speaker_name"
        ),

        speaker_bio=data.get(
            "speaker_bio"
        ),

        speaker_avatar_url=data.get(
            "speaker_avatar_url"
        ),

        session_type=session_type,

        room=data.get(
            "room"
        ),

        starts_at=starts_at,

        ends_at=ends_at,

        is_live=bool(
            data.get(
                "is_live",
                False
            )
        ),

        stream_url=data.get(
            "stream_url"
        ),

        created_by=user,

        created_at=datetime.now(
            timezone.utc
        )

    )

    session.save()

    return jsonify({

        "message":
            "Session created successfully",

        "session":
            session.to_dict()

    }), 201


# ═════════════════════════════════════════════════════════════
# LIST SESSIONS
# ═════════════════════════════════════════════════════════════

@sessions_bp.route(
    "",
    methods=["GET"]
)
def list_sessions():
    """
    List sessions
    ---
    tags:
      - Sessions
    """

    query = Session.objects()

    event_id = request.args.get(
        "event_id"
    )

    if event_id:

        event = Event.objects(
            id=event_id
        ).first()

        if event:

            query = query.filter(
                event=event
            )

    session_type = request.args.get(
        "session_type"
    )

    if session_type:

        query = query.filter(
            session_type=session_type
        )

    is_live = request.args.get(
        "is_live"
    )

    if is_live == "true":

        query = query.filter(
            is_live=True
        )

    sessions = query.order_by(
        "starts_at"
    )

    return jsonify({

        "total":
            sessions.count(),

        "sessions": [
            session.to_dict()
            for session in sessions
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# GET SESSION
# ═════════════════════════════════════════════════════════════

@sessions_bp.route(
    "/<session_id>",
    methods=["GET"]
)
def get_session(session_id):
    """
    Get session details
    ---
    tags:
      - Sessions
    """

    session = get_object_or_404(

        Session,

        id=session_id,

        description=
            "Session not found"

    )

    return jsonify({
        "session":
            session.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# UPDATE SESSION
# ═════════════════════════════════════════════════════════════

@sessions_bp.route(
    "/<session_id>",
    methods=["PUT"]
)
@jwt_required()
@role_required("organizer", "admin")
def update_session(session_id):
    """
    Update session
    ---
    tags:
      - Sessions
    security:
      - Bearer: []
    """

    session = get_object_or_404(

        Session,

        id=session_id,

        description=
            "Session not found"

    )

    user = get_current_user()

    if (

        user.role != "admin"

        and

        str(session.created_by.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "You can only update "
                "your own sessions"
        }), 403

    data = request.get_json()

    editable_fields = [

        "title",

        "description",

        "speaker_name",

        "speaker_bio",

        "speaker_avatar_url",

        "room",

        "stream_url"

    ]

    for field in editable_fields:

        if field in data:

            setattr(
                session,
                field,
                data[field]
            )

    if "session_type" in data:

        if data["session_type"] not in SESSION_TYPES:

            return jsonify({
                "error":
                    f"session_type must be "
                    f"one of {SESSION_TYPES}"
            }), 400

        session.session_type = data[
            "session_type"
        ]

    if "starts_at" in data:

        parsed_start = parse_datetime(
            data["starts_at"]
        )

        if not parsed_start:

            return jsonify({
                "error":
                    "starts_at must be "
                    "'YYYY-MM-DD HH:MM'"
            }), 400

        session.starts_at = parsed_start

    if "ends_at" in data:

        parsed_end = parse_datetime(
            data["ends_at"]
        )

        if not parsed_end:

            return jsonify({
                "error":
                    "ends_at must be "
                    "'YYYY-MM-DD HH:MM'"
            }), 400

        session.ends_at = parsed_end

    if (

        session.ends_at
        and
        session.starts_at
        and
        session.ends_at <= session.starts_at

    ):

        return jsonify({
            "error":
                "ends_at must be after starts_at"
        }), 400

    if "is_live" in data:

        session.is_live = bool(
            data["is_live"]
        )

    session.updated_at = datetime.now(
        timezone.utc
    )

    session.save()

    return jsonify({

        "message":
            "Session updated successfully",

        "session":
            session.to_dict()

    }), 200


# ═════════════════════════════════════════════════════════════
# DELETE SESSION
# ═════════════════════════════════════════════════════════════

@sessions_bp.route(
    "/<session_id>",
    methods=["DELETE"]
)
@jwt_required()
@role_required("organizer", "admin")
def delete_session(session_id):
    """
    Delete session
    ---
    tags:
      - Sessions
    security:
      - Bearer: []
    """

    session = get_object_or_404(

        Session,

        id=session_id,

        description=
            "Session not found"

    )

    user = get_current_user()

    if (

        user.role != "admin"

        and

        str(session.created_by.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "You can only delete "
                "your own sessions"
        }), 403

    session.delete()

    return jsonify({
        "message":
            "Session deleted successfully"
    }), 200


# ═════════════════════════════════════════════════════════════
# SESSION ANALYTICS
# ═════════════════════════════════════════════════════════════

@sessions_bp.route(
    "/analytics/overview",
    methods=["GET"]
)
@jwt_required()
def session_analytics():
    """
    Session analytics
    ---
    tags:
      - Session Analytics
    security:
      - Bearer: []
    """

    total_sessions = (
        Session.objects.count()
    )

    live_sessions = (
        Session.objects(
            is_live=True
        ).count()
    )

    keynote_sessions = (
        Session.objects(
            session_type="keynote"
        ).count()
    )

    workshop_sessions = (
        Session.objects(
            session_type="workshop"
        ).count()
    )

    panel_sessions = (
        Session.objects(
            session_type="panel"
        ).count()
    )

    networking_sessions = (
        Session.objects(
            session_type="networking"
        ).count()
    )

    break_sessions = (
        Session.objects(
            session_type="break"
        ).count()
    )

    return jsonify({

        "total_sessions":
            total_sessions,

        "live_sessions":
            live_sessions,

        "keynote_sessions":
            keynote_sessions,

        "workshop_sessions":
            workshop_sessions,

        "panel_sessions":
            panel_sessions,

        "networking_sessions":
            networking_sessions,

        "break_sessions":
            break_sessions

    }), 200


# ═════════════════════════════════════════════════════════════
# LIVE SESSIONS
# ═════════════════════════════════════════════════════════════

@sessions_bp.route(
    "/live/all",
    methods=["GET"]
)
def live_sessions():
    """
    Get all live sessions
    ---
    tags:
      - Sessions
    """

    sessions = Session.objects(
        is_live=True
    ).order_by("starts_at")

    return jsonify({

        "total":
            sessions.count(),

        "sessions": [
            session.to_dict()
            for session in sessions
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# EVENT TIMELINE
# ═════════════════════════════════════════════════════════════

@sessions_bp.route(
    "/event/<event_id>/timeline",
    methods=["GET"]
)
def event_timeline(event_id):
    """
    Event session timeline
    ---
    tags:
      - Sessions
    """

    event = get_object_or_404(

        Event,

        id=event_id,

        description=
            "Event not found"

    )

    sessions = Session.objects(
        event=event
    ).order_by("starts_at")

    return jsonify({

        "event_id":
            str(event.id),

        "event_title":
            event.title,

        "timeline": [
            session.to_dict()
            for session in sessions
        ]

    }), 200