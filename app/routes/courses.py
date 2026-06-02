from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Course
from app.utils import role_required, get_current_user, get_object_or_404

courses_bp = Blueprint("courses", __name__)


@courses_bp.route("", methods=["POST"])
@jwt_required()
@role_required("conductor", "admin")
def create_course():
    """Create Course --- tags: [Courses] security: [{Bearer: []}]"""
    data = request.get_json()
    for field in ["title", "description", "price"]:
        if data.get(field) is None:
            return jsonify({"error": f"{field} is required"}), 400
    user = get_current_user()
    course = Course(title=data["title"], description=data["description"],
                    price=float(data["price"]), duration=data.get("duration"),
                    instructor=data.get("instructor"), category=data.get("category"),
                    created_by=user)
    course.save()
    return jsonify({"message": "Course created", "course": course.to_dict()}), 201


@courses_bp.route("", methods=["GET"])
def get_all_courses():
    """Get All Courses --- tags: [Courses]"""
    category = request.args.get("category")
    qs = Course.objects(category=category) if category else Course.objects()
    courses = qs.order_by("-created_at")
    return jsonify({"courses": [c.to_dict() for c in courses]}), 200


@courses_bp.route("/<course_id>", methods=["GET"])
def get_course(course_id):
    """Get Course --- tags: [Courses]"""
    course = get_object_or_404(Course, id=course_id, description="Course not found")
    return jsonify({"course": course.to_dict()}), 200


@courses_bp.route("/<course_id>", methods=["PUT"])
@jwt_required()
@role_required("conductor", "admin")
def update_course(course_id):
    """Update Course --- tags: [Courses] security: [{Bearer: []}]"""
    course = get_object_or_404(Course, id=course_id, description="Course not found")
    user = get_current_user()
    if user.role != "admin" and str(course.created_by.id) != str(user.id):
        return jsonify({"error": "You can only update your own courses"}), 403
    data = request.get_json()
    for field in ["title", "description", "duration", "instructor", "category"]:
        if field in data:
            setattr(course, field, data[field])
    if "price" in data:
        course.price = float(data["price"])
    course.save()
    return jsonify({"message": "Course updated", "course": course.to_dict()}), 200


@courses_bp.route("/<course_id>", methods=["DELETE"])
@jwt_required()
@role_required("conductor", "admin")
def delete_course(course_id):
    """Delete Course --- tags: [Courses] security: [{Bearer: []}]"""
    course = get_object_or_404(Course, id=course_id, description="Course not found")
    user = get_current_user()
    if user.role != "admin" and str(course.created_by.id) != str(user.id):
        return jsonify({"error": "You can only delete your own courses"}), 403
    course.delete()
    return jsonify({"message": "Course deleted"}), 200


@courses_bp.route("/<course_id>/purchase", methods=["POST"])
@jwt_required()
def purchase_info(course_id):
    """Purchase Info --- tags: [Courses] security: [{Bearer: []}]"""
    course = get_object_or_404(Course, id=course_id, description="Course not found")
    return jsonify({"message": "Use POST /payments/create-order to purchase",
                    "course_id": str(course.id), "title": course.title, "price": course.price}), 200