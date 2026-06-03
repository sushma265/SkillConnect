"""
SkillConnect – Poll Routes
=============================
Advanced live polling and voting system with:
- Poll creation
- Single & multiple choice voting
- Real-time poll results
- Poll analytics
- Session polling
- Vote validation
- Poll management
- Live audience engagement
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

from app.models.poll_model import (
    Poll,
    PollOption,
    PollVote
)

from app.models.session_model import Session

from app.utils.decorators import (
    role_required
)

from app.utils.jwt_utils import (
    get_current_user,
    get_object_or_404
)

polls_bp = Blueprint(
    "polls",
    __name__
)

DATE_FMT = "%Y-%m-%d %H:%M"


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
# CREATE POLL
# ═════════════════════════════════════════════════════════════

@polls_bp.route(
    "",
    methods=["POST"]
)
@jwt_required()
@role_required("organizer", "admin")
def create_poll():
    """
    Create poll
    ---
    tags:
      - Polls
    security:
      - Bearer: []
    """

    data = request.get_json()

    required_fields = [

        "session_id",

        "question",

        "options"

    ]

    for field in required_fields:

        if not data.get(field):

            return jsonify({
                "error":
                    f"{field} is required"
            }), 400

    options = data["options"]

    if (
        not isinstance(options, list)
        or len(options) < 2
    ):

        return jsonify({
            "error":
                "At least 2 options required"
        }), 400

    session = get_object_or_404(

        Session,

        id=data["session_id"],

        description=
            "Session not found"

    )

    user = get_current_user()

    closes_at = None

    if data.get("closes_at"):

        closes_at = parse_datetime(
            data["closes_at"]
        )

        if not closes_at:

            return jsonify({
                "error":
                    "closes_at must be "
                    "'YYYY-MM-DD HH:MM'"
            }), 400

    poll = Poll(

        session=session,

        question=data[
            "question"
        ].strip(),

        is_multiple_choice=bool(

            data.get(
                "is_multiple_choice",
                False
            )

        ),

        is_active=True,

        closes_at=closes_at,

        created_by=user,

        created_at=datetime.now(
            timezone.utc
        )

    )

    poll.save()

    # Create poll options

    for index, option_text in enumerate(options):

        option = PollOption(

            poll_id=str(poll.id),

            text=str(
                option_text
            ).strip(),

            order=index

        )

        option.save()

    return jsonify({

        "message":
            "Poll created successfully",

        "poll":
            poll.to_dict()

    }), 201


# ═════════════════════════════════════════════════════════════
# LIST POLLS
# ═════════════════════════════════════════════════════════════

@polls_bp.route(
    "",
    methods=["GET"]
)
def list_polls():
    """
    List session polls
    ---
    tags:
      - Polls
    """

    session_id = request.args.get(
        "session_id"
    )

    if not session_id:

        return jsonify({
            "error":
                "session_id query param "
                "is required"
        }), 400

    session = Session.objects(
        id=session_id
    ).first()

    if not session:

        return jsonify({
            "polls": []
        }), 200

    active_only = request.args.get(
        "active_only"
    )

    query = Poll.objects(
        session=session
    )

    if active_only == "true":

        query = query.filter(
            is_active=True
        )

    polls = query.order_by(
        "-created_at"
    )

    return jsonify({

        "total":
            polls.count(),

        "polls": [
            poll.to_dict()
            for poll in polls
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# GET SINGLE POLL
# ═════════════════════════════════════════════════════════════

@polls_bp.route(
    "/<poll_id>",
    methods=["GET"]
)
def get_poll(poll_id):
    """
    Get poll details
    ---
    tags:
      - Polls
    """

    poll = get_object_or_404(

        Poll,

        id=poll_id,

        description=
            "Poll not found"

    )

    return jsonify({

        "poll":
            poll.to_dict(
                include_results=True
            )

    }), 200


# ═════════════════════════════════════════════════════════════
# VOTE ON POLL
# ═════════════════════════════════════════════════════════════

@polls_bp.route(
    "/vote",
    methods=["POST"]
)
@jwt_required()
def vote_on_poll():
    """
    Vote on poll
    ---
    tags:
      - Polls
    security:
      - Bearer: []
    """

    data = request.get_json()

    poll_id = data.get(
        "poll_id"
    )

    option_ids = data.get(
        "option_ids",
        []
    )

    if not poll_id:

        return jsonify({
            "error":
                "poll_id is required"
        }), 400

    poll = get_object_or_404(

        Poll,

        id=poll_id,

        description=
            "Poll not found"

    )

    # Check active

    if not poll.is_active:

        return jsonify({
            "error":
                "This poll is closed"
        }), 400

    # Check expiry

    if poll.closes_at:

        closes_at_utc = poll.closes_at.replace(
            tzinfo=timezone.utc
        )

        if (
            datetime.now(timezone.utc)
            > closes_at_utc
        ):

            poll.is_active = False

            poll.save()

            return jsonify({
                "error":
                    "Poll has expired"
            }), 400

    if (
        not option_ids
        or not isinstance(
            option_ids,
            list
        )
    ):

        return jsonify({
            "error":
                "option_ids must be "
                "a non-empty list"
        }), 400

    if (

        not poll.is_multiple_choice

        and

        len(option_ids) > 1

    ):

        return jsonify({
            "error":
                "This is a single-choice poll"
        }), 400

    user = get_current_user()

    existing_vote = PollVote.objects(

        poll=poll,

        user=user

    ).first()

    if existing_vote:

        return jsonify({
            "error":
                "You already voted"
        }), 409

    valid_option_ids = {

        str(option.id)

        for option in PollOption.objects(
            poll_id=str(poll.id)
        )

    }

    for option_id in option_ids:

        if str(option_id) not in valid_option_ids:

            return jsonify({
                "error":
                    f"Option {option_id} "
                    "does not belong to poll"
            }), 400

    # Save votes

    for option_id in option_ids:

        option = PollOption.objects(
            id=str(option_id)
        ).first()

        if option:

            vote = PollVote(

                poll=poll,

                option=option,

                user=user,

                created_at=datetime.now(
                    timezone.utc
                )

            )

            vote.save()

    return jsonify({

        "message":
            "Vote submitted successfully",

        "poll":
            poll.to_dict(
                include_results=True
            )

    }), 201


# ═════════════════════════════════════════════════════════════
# VOTE USING URL
# ═════════════════════════════════════════════════════════════

@polls_bp.route(
    "/<poll_id>/vote",
    methods=["POST"]
)
@jwt_required()
def vote_specific_poll(poll_id):
    """
    Vote on specific poll
    ---
    tags:
      - Polls
    security:
      - Bearer: []
    """

    data = request.get_json() or {}

    data["poll_id"] = poll_id

    request._cached_json = data

    return vote_on_poll()


# ═════════════════════════════════════════════════════════════
# POLL RESULTS
# ═════════════════════════════════════════════════════════════

@polls_bp.route(
    "/results/<poll_id>",
    methods=["GET"]
)
def poll_results(poll_id):
    """
    Get poll results
    ---
    tags:
      - Polls
    """

    poll = get_object_or_404(

        Poll,

        id=poll_id,

        description=
            "Poll not found"

    )

    return jsonify({

        "poll":
            poll.to_dict(
                include_results=True
            )

    }), 200


# ═════════════════════════════════════════════════════════════
# CLOSE POLL
# ═════════════════════════════════════════════════════════════

@polls_bp.route(
    "/<poll_id>/close",
    methods=["PUT"]
)
@jwt_required()
@role_required("organizer", "admin")
def close_poll(poll_id):
    """
    Close poll
    ---
    tags:
      - Polls
    security:
      - Bearer: []
    """

    poll = get_object_or_404(

        Poll,

        id=poll_id,

        description=
            "Poll not found"

    )

    poll.is_active = False

    poll.closed_at = datetime.now(
        timezone.utc
    )

    poll.save()

    return jsonify({

        "message":
            "Poll closed successfully",

        "poll":
            poll.to_dict(
                include_results=True
            )

    }), 200


# ═════════════════════════════════════════════════════════════
# DELETE POLL
# ═════════════════════════════════════════════════════════════

@polls_bp.route(
    "/<poll_id>",
    methods=["DELETE"]
)
@jwt_required()
@role_required("organizer", "admin")
def delete_poll(poll_id):
    """
    Delete poll
    ---
    tags:
      - Polls
    security:
      - Bearer: []
    """

    poll = get_object_or_404(

        Poll,

        id=poll_id,

        description=
            "Poll not found"

    )

    PollOption.objects(
        poll_id=poll_id
    ).delete()

    PollVote.objects(
        poll=poll
    ).delete()

    poll.delete()

    return jsonify({
        "message":
            "Poll deleted successfully"
    }), 200


# ═════════════════════════════════════════════════════════════
# POLL ANALYTICS
# ═════════════════════════════════════════════════════════════

@polls_bp.route(
    "/analytics/overview",
    methods=["GET"]
)
@jwt_required()
def poll_analytics():
    """
    Poll analytics
    ---
    tags:
      - Poll Analytics
    security:
      - Bearer: []
    """

    total_polls = (
        Poll.objects.count()
    )

    active_polls = (
        Poll.objects(
            is_active=True
        ).count()
    )

    total_votes = (
        PollVote.objects.count()
    )

    multiple_choice_polls = (
        Poll.objects(
            is_multiple_choice=True
        ).count()
    )

    single_choice_polls = (
        Poll.objects(
            is_multiple_choice=False
        ).count()
    )

    return jsonify({

        "total_polls":
            total_polls,

        "active_polls":
            active_polls,

        "total_votes":
            total_votes,

        "multiple_choice_polls":
            multiple_choice_polls,

        "single_choice_polls":
            single_choice_polls,

    }), 200


# ═════════════════════════════════════════════════════════════
# RECENT POLLS
# ═════════════════════════════════════════════════════════════

@polls_bp.route(
    "/recent",
    methods=["GET"]
)
def recent_polls():
    """
    Get recent polls
    ---
    tags:
      - Polls
    """

    limit = int(
        request.args.get(
            "limit",
            10
        )
    )

    polls = Poll.objects.order_by(
        "-created_at"
    )[:limit]

    return jsonify({

        "polls": [
            poll.to_dict(
                include_results=True
            )
            for poll in polls
        ]

    }), 200