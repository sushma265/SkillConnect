from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Course
from app.utils import role_required, get_current_user

courses_bp = Blueprint("courses", __name__)


@courses_bp.route("", methods=["POST"])
@jwt_required()
@role_required("conductor", "admin")
def create_course():
    """
    Create Course API
    ---
    tags:
      - Courses

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
            - title
            - description
            - price

          properties:
            title:
              type: string
              example: Python Masterclass

            description:
              type: string
              example: Complete Python course

            price:
              type: number
              example: 999

            duration:
              type: string
              example: 3 Months

            instructor:
              type: string
              example: John Doe

            category:
              type: string
              example: Programming

    responses:
      201:
        description: Course created successfully

      400:
        description: Missing required fields

      401:
        description: Unauthorized

      403:
        description: Access denied
    """

    data = request.get_json()

    required = ["title", "description", "price"]

    for field in required:
        if data.get(field) is None:
            return jsonify({
                "error": f"{field} is required"
            }), 400

    user_id = get_jwt_identity()

    course = Course(
        title=data["title"],
        description=data["description"],
        price=float(data["price"]),
        duration=data.get("duration"),
        instructor=data.get("instructor"),
        category=data.get("category"),
        created_by=int(user_id),
    )

    db.session.add(course)
    db.session.commit()

    return jsonify({
        "message": "Course created",
        "course": course.to_dict()
    }), 201


@courses_bp.route("", methods=["GET"])
def get_all_courses():
    """
    Get All Courses API
    ---
    tags:
      - Courses

    parameters:
      - name: category
        in: query
        type: string
        required: false
        example: Programming

    responses:
      200:
        description: List of all courses
    """

    category = request.args.get("category")

    query = Course.query

    if category:
        query = query.filter_by(category=category)

    courses = query.order_by(Course.created_at.desc()).all()

    return jsonify({
        "courses": [c.to_dict() for c in courses]
    }), 200


@courses_bp.route("/<int:course_id>", methods=["GET"])
def get_course(course_id):
    """
    Get Single Course API
    ---
    tags:
      - Courses

    parameters:
      - name: course_id
        in: path
        type: integer
        required: true

    responses:
      200:
        description: Course details returned

      404:
        description: Course not found
    """

    course = Course.query.get_or_404(
        course_id,
        description="Course not found"
    )

    return jsonify({
        "course": course.to_dict()
    }), 200


@courses_bp.route("/<int:course_id>", methods=["PUT"])
@jwt_required()
@role_required("conductor", "admin")
def update_course(course_id):
    """
    Update Course API
    ---
    tags:
      - Courses

    security:
      - Bearer: []

    parameters:
      - name: course_id
        in: path
        type: integer
        required: true

      - in: body
        name: body
        required: true

        schema:
          type: object

          properties:
            title:
              type: string

            description:
              type: string

            price:
              type: number

            duration:
              type: string

            instructor:
              type: string

            category:
              type: string

    responses:
      200:
        description: Course updated successfully

      403:
        description: Unauthorized to update

      404:
        description: Course not found
    """

    course = Course.query.get_or_404(
        course_id,
        description="Course not found"
    )

    user = get_current_user()

    if user.role != "admin" and course.created_by != user.id:
        return jsonify({
            "error": "You can only update your own courses"
        }), 403

    data = request.get_json()

    for field in [
        "title",
        "description",
        "duration",
        "instructor",
        "category"
    ]:
        if field in data:
            setattr(course, field, data[field])

    if "price" in data:
        course.price = float(data["price"])

    db.session.commit()

    return jsonify({
        "message": "Course updated",
        "course": course.to_dict()
    }), 200


@courses_bp.route("/<int:course_id>", methods=["DELETE"])
@jwt_required()
@role_required("conductor", "admin")
def delete_course(course_id):
    """
    Delete Course API
    ---
    tags:
      - Courses

    security:
      - Bearer: []

    parameters:
      - name: course_id
        in: path
        type: integer
        required: true

    responses:
      200:
        description: Course deleted successfully

      403:
        description: Unauthorized to delete

      404:
        description: Course not found
    """

    course = Course.query.get_or_404(
        course_id,
        description="Course not found"
    )

    user = get_current_user()

    if user.role != "admin" and course.created_by != user.id:
        return jsonify({
            "error": "You can only delete your own courses"
        }), 403

    db.session.delete(course)
    db.session.commit()

    return jsonify({
        "message": "Course deleted"
    }), 200


@courses_bp.route("/<int:course_id>/purchase", methods=["POST"])
@jwt_required()
def purchase_info(course_id):
    """
    Purchase Course API
    ---
    tags:
      - Courses

    security:
      - Bearer: []

    parameters:
      - name: course_id
        in: path
        type: integer
        required: true

    responses:
      200:
        description: Purchase information returned

      404:
        description: Course not found
    """

    course = Course.query.get_or_404(
        course_id,
        description="Course not found"
    )

    return jsonify({
        "message": "Use POST /payments/create-order to purchase this course",
        "course_id": course.id,
        "title": course.title,
        "price": course.price,
    }), 200