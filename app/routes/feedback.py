"""
SkillConnect – Feedback Routes
=================================
Advanced feedback management system with:
- Event & session feedback
- Ratings and reviews
- Analytics
- Feedback moderation
- Average ratings
- User feedback history
"""

from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required
)

from datetime import (
    datetime,
    timezone
)

from app.models.feedback_model import Feedback
from app.models.event_model import Event
from app.models.session_model import Session

from app.utils.jwt_utils import (
    get_current_user,
    get_object_or_404
)

from app.utils.decorators import (
    role_required
)

feedback_bp = Blueprint(
    "feedback",
    __name__
)


# ═════════════════════════════════════════════════════════════
# SUBMIT FEEDBACK
# ═════════════════════════════════════════════════════════════

@feedback_bp.route("", methods=["POST"])
@jwt_required()
def submit_feedback():
    """
    Submit feedback
    ---
    tags:
      - Feedback
    security:
      - Bearer: []
    """

    data = request.get_json()

    user = get_current_user()

    feedback_type = data.get(
        "feedback_type"
    )

    item_id = data.get(
        "item_id"
    )

    rating = data.get(
        "rating"
    )

    if feedback_type not in (
        "event",
        "session"
    ):

        return jsonify({
            "error":
                "feedback_type must be "
                "'event' or 'session'"
        }), 400

    if not item_id:

        return jsonify({
            "error":
                "item_id is required"
        }), 400

    if (
        rating is None
        or not isinstance(rating, int)
        or rating < 1
        or rating > 5
    ):

        return jsonify({
            "error":
                "rating must be "
                "between 1 and 5"
        }), 400

    # Prevent duplicate feedback

    existing_feedback = Feedback.objects(

        user=user,

        feedback_type=feedback_type,

        event=item_id if feedback_type == "event" else None,

        session=item_id if feedback_type == "session" else None

    ).first()

    if existing_feedback:

        return jsonify({
            "error":
                "Feedback already submitted"
        }), 409

    feedback_data = {

        "user": user,

        "rating": rating,

        "comment": data.get(
            "comment"
        ),

        "feedback_type":
            feedback_type,

        "created_at":
            datetime.now(
                timezone.utc
            )
    }

    # Event feedback

    if feedback_type == "event":

        event = Event.objects(
            id=item_id
        ).first()

        if not event:

            return jsonify({
                "error":
                    "Event not found"
            }), 404

        feedback_data["event"] = event

    # Session feedback

    else:

        session = Session.objects(
            id=item_id
        ).first()

        if not session:

            return jsonify({
                "error":
                    "Session not found"
            }), 404

        feedback_data["session"] = session

    feedback = Feedback(
        **feedback_data
    )

    feedback.save()

    return jsonify({

        "message":
            "Feedback submitted successfully",

        "feedback":
            feedback.to_dict()

    }), 201


# ═════════════════════════════════════════════════════════════
# GET FEEDBACK
# ═════════════════════════════════════════════════════════════

@feedback_bp.route("", methods=["GET"])
def get_feedback():
    """
    Get feedback
    ---
    tags:
      - Feedback
    """

    feedback_type = request.args.get(
        "type"
    )

    item_id = request.args.get(
        "item_id"
    )

    min_rating = request.args.get(
        "min_rating"
    )

    query = Feedback.objects()

    if feedback_type in (
        "event",
        "session"
    ):

        query = query.filter(
            feedback_type=feedback_type
        )

    if item_id:

        if feedback_type == "event":

            event = Event.objects(
                id=item_id
            ).first()

            if event:
                query = query.filter(
                    event=event
                )

        elif feedback_type == "session":

            session = Session.objects(
                id=item_id
            ).first()

            if session:
                query = query.filter(
                    session=session
                )

    if min_rating:

        try:

            query = query.filter(
                rating__gte=int(
                    min_rating
                )
            )

        except Exception:
            pass

    feedbacks = query.order_by(
        "-created_at"
    )

    return jsonify({

        "total":
            feedbacks.count(),

        "feedback": [
            feedback.to_dict()
            for feedback in feedbacks
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# GET SINGLE FEEDBACK
# ═════════════════════════════════════════════════════════════

@feedback_bp.route(
    "/<feedback_id>",
    methods=["GET"]
)
def get_single_feedback(feedback_id):
    """
    Get single feedback
    ---
    tags:
      - Feedback
    """

    feedback = get_object_or_404(

        Feedback,

        id=feedback_id,

        description=
            "Feedback not found"

    )

    return jsonify({
        "feedback":
            feedback.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# UPDATE FEEDBACK
# ═════════════════════════════════════════════════════════════

@feedback_bp.route(
    "/<feedback_id>",
    methods=["PUT"]
)
@jwt_required()
def update_feedback(feedback_id):
    """
    Update feedback
    ---
    tags:
      - Feedback
    security:
      - Bearer: []
    """

    feedback = get_object_or_404(

        Feedback,

        id=feedback_id,

        description=
            "Feedback not found"

    )

    user = get_current_user()

    if (
        str(feedback.user.id)
        != str(user.id)
    ):

        return jsonify({
            "error":
                "You can only update "
                "your own feedback"
        }), 403

    data = request.get_json()

    if "rating" in data:

        rating = data["rating"]

        if (
            not isinstance(rating, int)
            or rating < 1
            or rating > 5
        ):

            return jsonify({
                "error":
                    "rating must be "
                    "between 1 and 5"
            }), 400

        feedback.rating = rating

    if "comment" in data:

        feedback.comment = data[
            "comment"
        ]

    feedback.updated_at = datetime.now(
        timezone.utc
    )

    feedback.save()

    return jsonify({

        "message":
            "Feedback updated successfully",

        "feedback":
            feedback.to_dict()

    }), 200


# ═════════════════════════════════════════════════════════════
# DELETE FEEDBACK
# ═════════════════════════════════════════════════════════════

@feedback_bp.route(
    "/<feedback_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_feedback(feedback_id):
    """
    Delete feedback
    ---
    tags:
      - Feedback
    security:
      - Bearer: []
    """

    feedback = get_object_or_404(

        Feedback,

        id=feedback_id,

        description=
            "Feedback not found"

    )

    user = get_current_user()

    if (
        str(feedback.user.id)
        != str(user.id)
        and user.role != "admin"
    ):

        return jsonify({
            "error":
                "Unauthorized"
        }), 403

    feedback.delete()

    return jsonify({
        "message":
            "Feedback deleted successfully"
    }), 200


# ═════════════════════════════════════════════════════════════
# MY FEEDBACK
# ═════════════════════════════════════════════════════════════

@feedback_bp.route(
    "/my-feedback",
    methods=["GET"]
)
@jwt_required()
def my_feedback():
    """
    Get current user's feedback
    ---
    tags:
      - Feedback
    security:
      - Bearer: []
    """

    user = get_current_user()

    feedbacks = Feedback.objects(
        user=user
    ).order_by("-created_at")

    return jsonify({

        "total":
            feedbacks.count(),

        "feedback": [
            feedback.to_dict()
            for feedback in feedbacks
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# FEEDBACK ANALYTICS
# ═════════════════════════════════════════════════════════════

@feedback_bp.route(
    "/analytics/overview",
    methods=["GET"]
)
@jwt_required()
@role_required("admin")
def feedback_analytics():
    """
    Feedback analytics
    ---
    tags:
      - Feedback Analytics
    security:
      - Bearer: []
    """

    feedbacks = Feedback.objects()

    total_feedback = feedbacks.count()

    ratings = [
        feedback.rating
        for feedback in feedbacks
    ]

    average_rating = round(
        sum(ratings) / len(ratings),
        2
    ) if ratings else 0

    five_star = Feedback.objects(
        rating=5
    ).count()

    four_star = Feedback.objects(
        rating=4
    ).count()

    three_star = Feedback.objects(
        rating=3
    ).count()

    two_star = Feedback.objects(
        rating=2
    ).count()

    one_star = Feedback.objects(
        rating=1
    ).count()

    return jsonify({

        "total_feedback":
            total_feedback,

        "average_rating":
            average_rating,

        "ratings_distribution": {

            "5_star":
                five_star,

            "4_star":
                four_star,

            "3_star":
                three_star,

            "2_star":
                two_star,

            "1_star":
                one_star,

        }

    }), 200


# ═════════════════════════════════════════════════════════════
# EVENT FEEDBACK SUMMARY
# ═════════════════════════════════════════════════════════════

@feedback_bp.route(
    "/event/<event_id>/summary",
    methods=["GET"]
)
def event_feedback_summary(event_id):
    """
    Event feedback summary
    ---
    tags:
      - Feedback
    """

    event = get_object_or_404(

        Event,

        id=event_id,

        description=
            "Event not found"

    )

    feedbacks = Feedback.objects(
        event=event
    )

    ratings = [
        feedback.rating
        for feedback in feedbacks
    ]

    average_rating = round(
        sum(ratings) / len(ratings),
        2
    ) if ratings else 0

    return jsonify({

        "event":
            event.title,

        "total_feedback":
            feedbacks.count(),

        "average_rating":
            average_rating,

        "feedback": [
            feedback.to_dict()
            for feedback in feedbacks
        ]

    }), 200