"""
SkillConnect – Question Routes
=================================
Session Q&A with upvoting, answers, and moderation.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timezone

from app.models.question_model import Question
from app.models.session_model import Session
from app.utils.decorators import role_required
from app.utils.jwt_utils import get_current_user, get_object_or_404

questions_bp = Blueprint("questions", __name__)


# ── POST /questions ─────────────────────────────────────────────────────
@questions_bp.route("", methods=["POST"])
@jwt_required()
def submit_question():
    """
    Submit a question during a session.
    ---
    tags: [Questions]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [session_id, content]
          properties:
            session_id:   {type: string}
            content:      {type: string}
            is_anonymous: {type: boolean}
    responses:
      201: {description: Question submitted}
    """
    data = request.get_json()

    for field in ["session_id", "content"]:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    session = get_object_or_404(
        Session, id=data["session_id"],
        description="Session not found",
    )
    user = get_current_user()

    q = Question(
        session=session,
        user=user,
        content=data["content"].strip(),
        is_anonymous=bool(data.get("is_anonymous", False)),
    )
    q.save()

    return jsonify({
        "message": "Question submitted",
        "question": q.to_dict(),
    }), 201


# ── GET /questions/<session_id> ─────────────────────────────────────────
@questions_bp.route("/<session_id>", methods=["GET"])
def list_questions(session_id):
    """
    Get all questions for a session.
    ---
    tags: [Questions]
    """
    session = Session.objects(id=session_id).first()
    if not session:
        return jsonify({"questions": []}), 200

    qs = Question.objects(session=session)

    if request.args.get("is_answered") == "true":
        qs = qs.filter(is_answered=True)
    elif request.args.get("is_answered") == "false":
        qs = qs.filter(is_answered=False)

    questions = qs.order_by("-upvotes", "created_at")
    return jsonify({
        "questions": [q.to_dict() for q in questions]
    }), 200


# ── POST /questions/<question_id>/upvote ────────────────────────────────
@questions_bp.route("/<question_id>/upvote", methods=["POST"])
@jwt_required()
def upvote_question(question_id):
    """
    Upvote a question.
    ---
    tags: [Questions]
    security: [{Bearer: []}]
    """
    question = get_object_or_404(
        Question, id=question_id,
        description="Question not found",
    )
    user = get_current_user()

    if user in question.upvoted_by:
        return jsonify({
            "error": "You have already upvoted this question"
        }), 409

    question.upvoted_by.append(user)
    question.upvotes += 1
    question.save()

    return jsonify({
        "message": "Upvoted",
        "upvotes": question.upvotes,
    }), 200


# ── DELETE /questions/<question_id>/upvote ──────────────────────────────
@questions_bp.route("/<question_id>/upvote", methods=["DELETE"])
@jwt_required()
def remove_upvote(question_id):
    """
    Remove an upvote from a question.
    ---
    tags: [Questions]
    security: [{Bearer: []}]
    """
    question = get_object_or_404(
        Question, id=question_id,
        description="Question not found",
    )
    user = get_current_user()

    if user not in question.upvoted_by:
        return jsonify({
            "error": "You haven't upvoted this question"
        }), 404

    question.upvoted_by.remove(user)
    question.upvotes = max(0, question.upvotes - 1)
    question.save()

    return jsonify({
        "message": "Upvote removed",
        "upvotes": question.upvotes,
    }), 200


# ── PUT /questions/<question_id>/answer ─────────────────────────────────
@questions_bp.route("/<question_id>/answer", methods=["PUT"])
@jwt_required()
@role_required("organizer", "admin")
def answer_question(question_id):
    """
    Answer a question (organizer/admin only).
    ---
    tags: [Questions]
    security: [{Bearer: []}]
    """
    question = get_object_or_404(
        Question, id=question_id,
        description="Question not found",
    )
    user = get_current_user()
    data = request.get_json() or {}

    question.is_answered = True
    question.answer = data.get("answer", "").strip() or None
    question.answered_by = user
    question.answered_at = datetime.now(timezone.utc)
    question.save()

    return jsonify({
        "message": "Question answered",
        "question": question.to_dict(),
    }), 200


# ── DELETE /questions/<question_id> ─────────────────────────────────────
@questions_bp.route("/<question_id>", methods=["DELETE"])
@jwt_required()
def delete_question(question_id):
    """
    Delete a question (own or organizer/admin).
    ---
    tags: [Questions]
    security: [{Bearer: []}]
    """
    question = get_object_or_404(
        Question, id=question_id,
        description="Question not found",
    )
    user = get_current_user()

    if (
        user.role not in ("admin", "organizer")
        and str(question.user.id) != str(user.id)
    ):
        return jsonify({
            "error": "You can only delete your own questions"
        }), 403

    question.delete()
    return jsonify({"message": "Question deleted"}), 200
