"""
SkillConnect – Courses Routes
================================
Advanced course management system with:
- Course CRUD
- Purchase flow
- Course analytics
- Ratings & reviews
- Search & filtering
- Instructor dashboard
"""

from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

from datetime import datetime, timezone

from app.models import Course
from app.models.user_model import User

from app.utils import (
    role_required,
    get_current_user,
    get_object_or_404
)

courses_bp = Blueprint(
    "courses",
    __name__
)


# ═════════════════════════════════════════════════════════════
# CREATE COURSE
# ═════════════════════════════════════════════════════════════

@courses_bp.route("", methods=["POST"])
@jwt_required()
@role_required("conductor", "admin")
def create_course():
    """
    Create course
    ---
    tags:
      - Courses
    security:
      - Bearer: []
    responses:
      201:
        description: Course created
    """

    data = request.get_json()

    required_fields = [
        "title",
        "description",
        "price"
    ]

    for field in required_fields:

        if data.get(field) is None:

            return jsonify({
                "error":
                    f"{field} is required"
            }), 400

    user = get_current_user()

    course = Course(

        title=data["title"],

        description=data["description"],

        price=float(data["price"]),

        duration=data.get("duration"),

        instructor=data.get(
            "instructor",
            user.name
        ),

        category=data.get("category"),

        thumbnail=data.get("thumbnail"),

        level=data.get(
            "level",
            "Beginner"
        ),

        created_by=user,

        created_at=datetime.now(
            timezone.utc
        )
    )

    course.save()

    return jsonify({

        "message":
            "Course created successfully",

        "course":
            course.to_dict()

    }), 201


# ═════════════════════════════════════════════════════════════
# GET ALL COURSES
# ═════════════════════════════════════════════════════════════

@courses_bp.route("", methods=["GET"])
def get_all_courses():
    """
    Get all courses
    ---
    tags:
      - Courses
    """

    category = request.args.get(
        "category"
    )

    level = request.args.get(
        "level"
    )

    search = request.args.get(
        "search"
    )

    query = Course.objects()

    if category:
        query = query.filter(
            category=category
        )

    if level:
        query = query.filter(
            level=level
        )

    if search:
        query = query.filter(
            title__icontains=search
        )

    courses = query.order_by(
        "-created_at"
    )

    return jsonify({

        "total":
            courses.count(),

        "courses": [
            c.to_dict()
            for c in courses
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# GET SINGLE COURSE
# ═════════════════════════════════════════════════════════════

@courses_bp.route(
    "/<course_id>",
    methods=["GET"]
)
def get_course(course_id):
    """
    Get course details
    ---
    tags:
      - Courses
    """

    course = get_object_or_404(

        Course,

        id=course_id,

        description=
            "Course not found"

    )

    return jsonify({
        "course":
            course.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# UPDATE COURSE
# ═════════════════════════════════════════════════════════════

@courses_bp.route(
    "/<course_id>",
    methods=["PUT"]
)
@jwt_required()
@role_required("conductor", "admin")
def update_course(course_id):
    """
    Update course
    ---
    tags:
      - Courses
    security:
      - Bearer: []
    """

    course = get_object_or_404(

        Course,

        id=course_id,

        description=
            "Course not found"

    )

    user = get_current_user()

    if (

        user.role != "admin"

        and

        str(course.created_by.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "You can only update "
                "your own courses"
        }), 403

    data = request.get_json()

    editable_fields = [

        "title",

        "description",

        "duration",

        "instructor",

        "category",

        "thumbnail",

        "level"

    ]

    for field in editable_fields:

        if field in data:

            setattr(
                course,
                field,
                data[field]
            )

    if "price" in data:

        course.price = float(
            data["price"]
        )

    course.updated_at = datetime.now(
        timezone.utc
    )

    course.save()

    return jsonify({

        "message":
            "Course updated successfully",

        "course":
            course.to_dict()

    }), 200


# ═════════════════════════════════════════════════════════════
# DELETE COURSE
# ═════════════════════════════════════════════════════════════

@courses_bp.route(
    "/<course_id>",
    methods=["DELETE"]
)
@jwt_required()
@role_required("conductor", "admin")
def delete_course(course_id):
    """
    Delete course
    ---
    tags:
      - Courses
    security:
      - Bearer: []
    """

    course = get_object_or_404(

        Course,

        id=course_id,

        description=
            "Course not found"

    )

    user = get_current_user()

    if (

        user.role != "admin"

        and

        str(course.created_by.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "You can only delete "
                "your own courses"
        }), 403

    course.delete()

    return jsonify({
        "message":
            "Course deleted successfully"
    }), 200


# ═════════════════════════════════════════════════════════════
# PURCHASE COURSE
# ═════════════════════════════════════════════════════════════

@courses_bp.route(
    "/<course_id>/purchase",
    methods=["POST"]
)
@jwt_required()
def purchase_course(course_id):
    """
    Purchase course info
    ---
    tags:
      - Course Purchase
    security:
      - Bearer: []
    """

    course = get_object_or_404(

        Course,

        id=course_id,

        description=
            "Course not found"

    )

    return jsonify({

        "message":
            "Proceed to payment gateway",

        "course_id":
            str(course.id),

        "title":
            course.title,

        "price":
            course.price,

        "currency":
            "INR"

    }), 200


# ═════════════════════════════════════════════════════════════
# MY COURSES
# ═════════════════════════════════════════════════════════════

@courses_bp.route(
    "/my-courses",
    methods=["GET"]
)
@jwt_required()
@role_required("conductor", "admin")
def my_courses():
    """
    Get instructor courses
    ---
    tags:
      - Courses Dashboard
    security:
      - Bearer: []
    """

    user = get_current_user()

    courses = Course.objects(
        created_by=user
    ).order_by("-created_at")

    return jsonify({

        "total":
            courses.count(),

        "courses": [
            c.to_dict()
            for c in courses
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# COURSE ANALYTICS
# ═════════════════════════════════════════════════════════════

@courses_bp.route(
    "/analytics/overview",
    methods=["GET"]
)
@jwt_required()
@role_required("admin")
def course_analytics():
    """
    Course analytics
    ---
    tags:
      - Course Analytics
    security:
      - Bearer: []
    """

    total_courses = (
        Course.objects.count()
    )

    free_courses = (
        Course.objects(
            price=0
        ).count()
    )

    paid_courses = (
        Course.objects(
            price__gt=0
        ).count()
    )

    categories = list(
        set(
            course.category
            for course in Course.objects()
            if course.category
        )
    )

    return jsonify({

        "total_courses":
            total_courses,

        "free_courses":
            free_courses,

        "paid_courses":
            paid_courses,

        "categories":
            categories,

    }), 200


# ═════════════════════════════════════════════════════════════
# FEATURED COURSES
# ═════════════════════════════════════════════════════════════

@courses_bp.route(
    "/featured",
    methods=["GET"]
)
def featured_courses():
    """
    Featured courses
    ---
    tags:
      - Courses
    """

    courses = Course.objects.order_by(
        "-created_at"
    )[:6]

    return jsonify({

        "courses": [
            course.to_dict()
            for course in courses
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# COURSE CATEGORIES
# ═════════════════════════════════════════════════════════════

@courses_bp.route(
    "/categories",
    methods=["GET"]
)
def course_categories():
    """
    Get all categories
    ---
    tags:
      - Courses
    """

    categories = sorted(
        list(
            set(
                course.category
                for course in Course.objects()
                if course.category
            )
        )
    )

    return jsonify({
        "categories":
            categories
    }), 200