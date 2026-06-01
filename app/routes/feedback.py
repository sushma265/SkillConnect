from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app import db
from app.models import Feedback, Course, Event
from app.utils import get_current_user

feedback_bp = Blueprint("feedback", __name__)


@feedback_bp.route("", methods=["POST"])
@jwt_required()
def submit_feedback():
    """
    Submit Feedback API
    ---
    tags:
      - Feedback

    security:
      - Bearer: []

    consumes:
      - application/json

    parameters:
      - in: body
        name: body
        required: true

        schema:
          type: object

          required:
            - feedback_type
            - item_id
            - rating

          properties:
            feedback_type:
              type: string
              example: course

            item_id:
              type: integer
              example: 1

            rating:
              type: integer
              example: 5

            comment:
              type: string
              example: Excellent course

    responses:
      201:
        description: Feedback submitted successfully

      400:
        description: Invalid request

      401:
        description: Unauthorized

      404:
        description: Course or Event not found
    """

    data = request.get_json()

    user = get_current_user()

    feedback_type = data.get("feedback_type")
    item_id = data.get("item_id")
    rating = data.get("rating")

    if feedback_type not in ("course", "event"):
        return jsonify({
            "error": "feedback_type must be 'course' or 'event'"
        }), 400

    if not item_id:
        return jsonify({
            "error": "item_id is required"
        }), 400

    if rating is None or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({
            "error": "rating must be an integer between 1 and 5"
        }), 400

    if feedback_type == "course":

        item = Course.query.get(item_id)

        if not item:
            return jsonify({
                "error": "Course not found"
            }), 404

        fb = Feedback(
            user_id=user.id,
            course_id=item_id,
            rating=rating,
            comment=data.get("comment"),
            feedback_type="course",
        )

    else:

        item = Event.query.get(item_id)

        if not item:
            return jsonify({
                "error": "Event not found"
            }), 404

        fb = Feedback(
            user_id=user.id,
            event_id=item_id,
            rating=rating,
            comment=data.get("comment"),
            feedback_type="event",
        )

    db.session.add(fb)
    db.session.commit()

    return jsonify({
        "message": "Feedback submitted",
        "feedback": fb.to_dict()
    }), 201


@feedback_bp.route("", methods=["GET"])
def get_feedback():
    """
    Get Feedback API
    ---
    tags:
      - Feedback

    parameters:
      - name: type
        in: query
        type: string
        required: false
        example: course

      - name: item_id
        in: query
        type: integer
        required: false
        example: 1

    responses:
      200:
        description: Feedback list returned
    """

    feedback_type = request.args.get("type")

    item_id = request.args.get("item_id", type=int)

    query = Feedback.query

    if feedback_type in ("course", "event"):
        query = query.filter_by(
            feedback_type=feedback_type
        )

    if item_id:

        if feedback_type == "course":
            query = query.filter_by(
                course_id=item_id
            )

        elif feedback_type == "event":
            query = query.filter_by(
                event_id=item_id
            )

    feedbacks = query.order_by(
        Feedback.created_at.desc()
    ).all()

    return jsonify({
        "feedback": [f.to_dict() for f in feedbacks]
    }), 200