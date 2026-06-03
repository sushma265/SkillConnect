"""
SkillConnect – Question Routes
=================================
Advanced Q&A management system with:
- Session questions
- Anonymous questions
- Upvoting system
- Question answering
- Moderation tools
- Question analytics
- Real-time engagement
- Question filtering
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

from app.models.question_model import Question
from app.models.session_model import Session

from app.utils.decorators import (
    role_required
)

from app.utils.jwt_utils import (
    get_current_user,
    get_object_or_404
)

questions_bp = Blueprint(
    "questions",
    __name__
)


# ═════════════════════════════════════════════════════════════
# SUBMIT QUESTION
# ═════════════════════════════════════════════════════════════

@questions_bp.route(
    "",
    methods=["POST"]
)
@jwt_required()
def submit_question():
    """
    Submit session question
    ---
    tags:
      - Questions
    security:
      - Bearer: []
    """

    data = request.get_json()

    required_fields = [

        "session_id",

        "content"

    ]

    for field in required_fields:

        if not data.get(field):

            return jsonify({
                "error":
                    f"{field} is required"
            }), 400

    session = get_object_or_404(

        Session,

        id=data["session_id"],

        description=
            "Session not found"

    )

    user = get_current_user()

    question = Question(

        session=session,

        user=user,

        content=data[
            "content"
        ].strip(),

        is_anonymous=bool(

            data.get(
                "is_anonymous",
                False
            )

        ),

        is_answered=False,

        upvotes=0,

        created_at=datetime.now(
            timezone.utc
        )

    )

    question.save()

    return jsonify({

        "message":
            "Question submitted successfully",

        "question":
            question.to_dict()

    }), 201


# ═════════════════════════════════════════════════════════════
# LIST QUESTIONS
# ═════════════════════════════════════════════════════════════

@questions_bp.route(
    "/<session_id>",
    methods=["GET"]
)
def list_questions(session_id):
    """
    Get session questions
    ---
    tags:
      - Questions
    """

    session = Session.objects(
        id=session_id
    ).first()

    if not session:

        return jsonify({
            "questions": []
        }), 200

    query = Question.objects(
        session=session
    )

    answered = request.args.get(
        "is_answered"
    )

    if answered == "true":

        query = query.filter(
            is_answered=True
        )

    elif answered == "false":

        query = query.filter(
            is_answered=False
        )

    questions = query.order_by(
        "-upvotes",
        "-created_at"
    )

    return jsonify({

        "total":
            questions.count(),

        "questions": [
            question.to_dict()
            for question in questions
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# GET SINGLE QUESTION
# ═════════════════════════════════════════════════════════════

@questions_bp.route(
    "/details/<question_id>",
    methods=["GET"]
)
def get_question(question_id):
    """
    Get question details
    ---
    tags:
      - Questions
    """

    question = get_object_or_404(

        Question,

        id=question_id,

        description=
            "Question not found"

    )

    return jsonify({
        "question":
            question.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# UPVOTE QUESTION
# ═════════════════════════════════════════════════════════════

@questions_bp.route(
    "/<question_id>/upvote",
    methods=["POST"]
)
@jwt_required()
def upvote_question(question_id):
    """
    Upvote question
    ---
    tags:
      - Questions
    security:
      - Bearer: []
    """

    question = get_object_or_404(

        Question,

        id=question_id,

        description=
            "Question not found"

    )

    user = get_current_user()

    if user in question.upvoted_by:

        return jsonify({
            "error":
                "Already upvoted"
        }), 409

    question.upvoted_by.append(
        user
    )

    question.upvotes += 1

    question.save()

    return jsonify({

        "message":
            "Question upvoted",

        "upvotes":
            question.upvotes

    }), 200


# ═════════════════════════════════════════════════════════════
# REMOVE UPVOTE
# ═════════════════════════════════════════════════════════════

@questions_bp.route(
    "/<question_id>/upvote",
    methods=["DELETE"]
)
@jwt_required()
def remove_upvote(question_id):
    """
    Remove question upvote
    ---
    tags:
      - Questions
    security:
      - Bearer: []
    """

    question = get_object_or_404(

        Question,

        id=question_id,

        description=
            "Question not found"

    )

    user = get_current_user()

    if user not in question.upvoted_by:

        return jsonify({
            "error":
                "You haven't upvoted"
        }), 404

    question.upvoted_by.remove(
        user
    )

    question.upvotes = max(
        0,
        question.upvotes - 1
    )

    question.save()

    return jsonify({

        "message":
            "Upvote removed",

        "upvotes":
            question.upvotes

    }), 200


# ═════════════════════════════════════════════════════════════
# ANSWER QUESTION
# ═════════════════════════════════════════════════════════════

@questions_bp.route(
    "/<question_id>/answer",
    methods=["PUT"]
)
@jwt_required()
@role_required("organizer", "admin")
def answer_question(question_id):
    """
    Answer question
    ---
    tags:
      - Questions
    security:
      - Bearer: []
    """

    question = get_object_or_404(

        Question,

        id=question_id,

        description=
            "Question not found"

    )

    user = get_current_user()

    data = request.get_json() or {}

    answer = data.get(
        "answer",
        ""
    ).strip()

    if not answer:

        return jsonify({
            "error":
                "answer is required"
        }), 400

    question.answer = answer

    question.is_answered = True

    question.answered_by = user

    question.answered_at = datetime.now(
        timezone.utc
    )

    question.save()

    return jsonify({

        "message":
            "Question answered successfully",

        "question":
            question.to_dict()

    }), 200


# ═════════════════════════════════════════════════════════════
# DELETE QUESTION
# ═════════════════════════════════════════════════════════════

@questions_bp.route(
    "/<question_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_question(question_id):
    """
    Delete question
    ---
    tags:
      - Questions
    security:
      - Bearer: []
    """

    question = get_object_or_404(

        Question,

        id=question_id,

        description=
            "Question not found"

    )

    user = get_current_user()

    if (

        user.role not in (
            "admin",
            "organizer"
        )

        and

        str(question.user.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "Unauthorized"
        }), 403

    question.delete()

    return jsonify({
        "message":
            "Question deleted successfully"
    }), 200


# ═════════════════════════════════════════════════════════════
# MY QUESTIONS
# ═════════════════════════════════════════════════════════════

@questions_bp.route(
    "/my/questions",
    methods=["GET"]
)
@jwt_required()
def my_questions():
    """
    Get user questions
    ---
    tags:
      - Questions
    security:
      - Bearer: []
    """

    user = get_current_user()

    questions = Question.objects(
        user=user
    ).order_by("-created_at")

    return jsonify({

        "total":
            questions.count(),

        "questions": [
            question.to_dict()
            for question in questions
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# QUESTION ANALYTICS
# ═════════════════════════════════════════════════════════════

@questions_bp.route(
    "/analytics/overview",
    methods=["GET"]
)
@jwt_required()
def question_analytics():
    """
    Question analytics
    ---
    tags:
      - Question Analytics
    security:
      - Bearer: []
    """

    total_questions = (
        Question.objects.count()
    )

    answered_questions = (
        Question.objects(
            is_answered=True
        ).count()
    )

    unanswered_questions = (
        Question.objects(
            is_answered=False
        ).count()
    )

    anonymous_questions = (
        Question.objects(
            is_anonymous=True
        ).count()
    )

    total_upvotes = 0

    all_questions = Question.objects()

    for question in all_questions:

        total_upvotes += int(
            question.upvotes
        )

    return jsonify({

        "total_questions":
            total_questions,

        "answered_questions":
            answered_questions,

        "unanswered_questions":
            unanswered_questions,

        "anonymous_questions":
            anonymous_questions,

        "total_upvotes":
            total_upvotes,

        "answer_rate":
            round(

                (
                    answered_questions
                    / total_questions
                ) * 100,

                2

            ) if total_questions > 0 else 0

    }), 200


# ═════════════════════════════════════════════════════════════
# TOP QUESTIONS
# ═════════════════════════════════════════════════════════════

@questions_bp.route(
    "/top",
    methods=["GET"]
)
def top_questions():
    """
    Get top questions
    ---
    tags:
      - Questions
    """

    limit = int(
        request.args.get(
            "limit",
            10
        )
    )

    questions = Question.objects.order_by(
        "-upvotes",
        "-created_at"
    )[:limit]

    return jsonify({

        "questions": [
            question.to_dict()
            for question in questions
        ]

    }), 200