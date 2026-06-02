"""
SkillConnect – Poll Routes
=============================
CRUD for session polls and voting.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timezone

from app.models.poll_model import Poll, PollOption, PollVote
from app.models.session_model import Session
from app.utils.decorators import role_required
from app.utils.jwt_utils import get_current_user, get_object_or_404

polls_bp = Blueprint("polls", __name__)
DATE_FMT = "%Y-%m-%d %H:%M"


def _parse_dt(s):
    """Parse a datetime string."""
    try:
        return datetime.strptime(s, DATE_FMT)
    except (ValueError, TypeError):
        return None


# ── POST /polls ─────────────────────────────────────────────────────────
@polls_bp.route("", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def create_poll():
    """
    Create a new poll for a session.
    ---
    tags: [Polls]
    security: [{Bearer: []}]
    """
    data = request.get_json()

    for field in ["session_id", "question", "options"]:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    options_list = data["options"]
    if not isinstance(options_list, list) or len(options_list) < 2:
        return jsonify({
            "error": "At least 2 options are required"
        }), 400

    session = get_object_or_404(
        Session, id=data["session_id"],
        description="Session not found",
    )
    user = get_current_user()

    closes_at = None
    if data.get("closes_at"):
        closes_at = _parse_dt(data["closes_at"])
        if not closes_at:
            return jsonify({
                "error": "closes_at must be 'YYYY-MM-DD HH:MM'"
            }), 400

    poll = Poll(
        session=session,
        question=data["question"].strip(),
        is_multiple_choice=bool(
            data.get("is_multiple_choice", False)
        ),
        is_active=True,
        closes_at=closes_at,
        created_by=user,
    )
    poll.save()

    # Create options
    for i, text in enumerate(options_list):
        opt = PollOption(
            poll_id=str(poll.id),
            text=str(text).strip(),
            order=i,
        )
        opt.save()

    return jsonify({
        "message": "Poll created",
        "poll": poll.to_dict(),
    }), 201


# ── POST /polls/vote ───────────────────────────────────────────────────
@polls_bp.route("/vote", methods=["POST"])
@jwt_required()
def vote_on_poll():
    """
    Cast a vote on a poll (via body: poll_id + option_ids).
    ---
    tags: [Polls]
    security: [{Bearer: []}]
    """
    data = request.get_json()
    poll_id = data.get("poll_id")
    option_ids = data.get("option_ids", [])

    if not poll_id:
        return jsonify({"error": "poll_id is required"}), 400

    poll = get_object_or_404(
        Poll, id=poll_id, description="Poll not found"
    )

    if not poll.is_active:
        return jsonify({"error": "This poll is closed"}), 400

    # Check expiry
    if poll.closes_at:
        closes_utc = poll.closes_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > closes_utc:
            poll.is_active = False
            poll.save()
            return jsonify({"error": "Poll has expired"}), 400

    if not option_ids or not isinstance(option_ids, list):
        return jsonify({
            "error": "option_ids must be a non-empty list"
        }), 400

    if not poll.is_multiple_choice and len(option_ids) > 1:
        return jsonify({
            "error": "This is a single-choice poll"
        }), 400

    user = get_current_user()
    if PollVote.objects(poll=poll, user=user).first():
        return jsonify({
            "error": "You have already voted on this poll"
        }), 409

    # Validate options belong to this poll
    valid_ids = {
        str(o.id) for o in PollOption.objects(poll_id=str(poll.id))
    }
    for oid in option_ids:
        if str(oid) not in valid_ids:
            return jsonify({
                "error": f"Option {oid} does not belong to this poll"
            }), 400

    # Cast votes
    for oid in option_ids:
        opt = PollOption.objects(id=str(oid)).first()
        if opt:
            PollVote(poll=poll, option=opt, user=user).save()

    return jsonify({
        "message": "Vote cast",
        "poll": poll.to_dict(include_results=True),
    }), 201


# ── GET /polls/results/<poll_id> ────────────────────────────────────────
@polls_bp.route("/results/<poll_id>", methods=["GET"])
def get_poll_results(poll_id):
    """
    Get poll results with vote counts.
    ---
    tags: [Polls]
    """
    poll = get_object_or_404(
        Poll, id=poll_id, description="Poll not found"
    )
    return jsonify({
        "poll": poll.to_dict(include_results=True)
    }), 200


# ── GET /polls ──────────────────────────────────────────────────────────
@polls_bp.route("", methods=["GET"])
def list_polls():
    """
    List polls for a session.
    ---
    tags: [Polls]
    """
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({
            "error": "session_id query param is required"
        }), 400

    session = Session.objects(id=session_id).first()
    if not session:
        return jsonify({"polls": []}), 200

    polls = Poll.objects(session=session).order_by("created_at")
    return jsonify({
        "polls": [p.to_dict() for p in polls]
    }), 200


# ── GET /polls/<poll_id> ───────────────────────────────────────────────
@polls_bp.route("/<poll_id>", methods=["GET"])
def get_poll(poll_id):
    """
    Get a single poll with results.
    ---
    tags: [Polls]
    """
    poll = get_object_or_404(
        Poll, id=poll_id, description="Poll not found"
    )
    return jsonify({
        "poll": poll.to_dict(include_results=True)
    }), 200


# ── POST /polls/<poll_id>/vote ──────────────────────────────────────────
@polls_bp.route("/<poll_id>/vote", methods=["POST"])
@jwt_required()
def vote_on_specific_poll(poll_id):
    """
    Cast a vote on a specific poll (via URL param).
    ---
    tags: [Polls]
    security: [{Bearer: []}]
    """
    poll = get_object_or_404(
        Poll, id=poll_id, description="Poll not found"
    )

    if not poll.is_active:
        return jsonify({"error": "This poll is closed"}), 400

    if poll.closes_at:
        closes_utc = poll.closes_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > closes_utc:
            poll.is_active = False
            poll.save()
            return jsonify({"error": "Poll has expired"}), 400

    data = request.get_json()
    option_ids = data.get("option_ids", [])

    if not option_ids or not isinstance(option_ids, list):
        return jsonify({
            "error": "option_ids must be a non-empty list"
        }), 400

    if not poll.is_multiple_choice and len(option_ids) > 1:
        return jsonify({
            "error": "This is a single-choice poll"
        }), 400

    user = get_current_user()
    if PollVote.objects(poll=poll, user=user).first():
        return jsonify({
            "error": "You have already voted on this poll"
        }), 409

    valid_ids = {
        str(o.id) for o in PollOption.objects(poll_id=str(poll.id))
    }
    for oid in option_ids:
        if str(oid) not in valid_ids:
            return jsonify({
                "error": f"Option {oid} does not belong to this poll"
            }), 400

    for oid in option_ids:
        opt = PollOption.objects(id=str(oid)).first()
        if opt:
            PollVote(poll=poll, option=opt, user=user).save()

    return jsonify({
        "message": "Vote cast",
        "poll": poll.to_dict(include_results=True),
    }), 201


# ── PUT /polls/<poll_id>/close ──────────────────────────────────────────
@polls_bp.route("/<poll_id>/close", methods=["PUT"])
@jwt_required()
@role_required("organizer", "admin")
def close_poll(poll_id):
    """
    Close a poll to stop accepting votes.
    ---
    tags: [Polls]
    security: [{Bearer: []}]
    """
    poll = get_object_or_404(
        Poll, id=poll_id, description="Poll not found"
    )
    poll.is_active = False
    poll.save()
    return jsonify({
        "message": "Poll closed",
        "poll": poll.to_dict(include_results=True),
    }), 200


# ── DELETE /polls/<poll_id> ─────────────────────────────────────────────
@polls_bp.route("/<poll_id>", methods=["DELETE"])
@jwt_required()
@role_required("organizer", "admin")
def delete_poll(poll_id):
    """
    Delete a poll and all its votes/options.
    ---
    tags: [Polls]
    security: [{Bearer: []}]
    """
    poll = get_object_or_404(
        Poll, id=poll_id, description="Poll not found"
    )
    PollOption.objects(poll_id=poll_id).delete()
    PollVote.objects(poll=poll).delete()
    poll.delete()
    return jsonify({"message": "Poll deleted"}), 200
