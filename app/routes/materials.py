"""
SkillConnect – Materials Routes
==================================
CRUD for session materials (PDFs, slides, links, videos).
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.models.material_model import SessionMaterial
from app.models.session_model import Session
from app.utils.decorators import role_required
from app.utils.jwt_utils import get_current_user, get_object_or_404

materials_bp = Blueprint("materials", __name__)
MATERIAL_TYPES = ("link", "pdf", "slide", "video", "image", "other")


# ── POST /materials ─────────────────────────────────────────────────────
@materials_bp.route("", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def add_material():
    """
    Upload / link a material to a session.
    ---
    tags: [Materials]
    security: [{Bearer: []}]
    """
    data = request.get_json()

    for field in ["session_id", "title", "url"]:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    session = get_object_or_404(
        Session, id=data["session_id"],
        description="Session not found",
    )

    material_type = data.get("material_type", "link")
    if material_type not in MATERIAL_TYPES:
        return jsonify({
            "error": f"material_type must be one of {MATERIAL_TYPES}"
        }), 400

    user = get_current_user()
    mat = SessionMaterial(
        session=session,
        title=data["title"],
        url=data["url"],
        material_type=material_type,
        description=data.get("description"),
        created_by=user,
    )
    mat.save()

    return jsonify({
        "message": "Material added",
        "material": mat.to_dict(),
    }), 201


# ── GET /materials ──────────────────────────────────────────────────────
@materials_bp.route("", methods=["GET"])
def list_materials():
    """
    List materials for a session.
    ---
    tags: [Materials]
    """
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({
            "error": "session_id query param is required"
        }), 400

    session = Session.objects(id=session_id).first()
    if not session:
        return jsonify({"materials": []}), 200

    qs = SessionMaterial.objects(session=session)
    if request.args.get("material_type"):
        qs = qs.filter(material_type=request.args["material_type"])

    return jsonify({
        "materials": [m.to_dict() for m in qs.order_by("created_at")]
    }), 200


# ── GET /materials/<id> ────────────────────────────────────────────────
@materials_bp.route("/<material_id>", methods=["GET"])
def get_material(material_id):
    """
    Get a single material by ID.
    ---
    tags: [Materials]
    """
    mat = get_object_or_404(
        SessionMaterial, id=material_id,
        description="Material not found",
    )
    return jsonify({"material": mat.to_dict()}), 200


# ── PUT /materials/<id> ────────────────────────────────────────────────
@materials_bp.route("/<material_id>", methods=["PUT"])
@jwt_required()
@role_required("organizer", "admin")
def update_material(material_id):
    """
    Update a material.
    ---
    tags: [Materials]
    security: [{Bearer: []}]
    """
    mat = get_object_or_404(
        SessionMaterial, id=material_id,
        description="Material not found",
    )
    user = get_current_user()

    if (
        user.role != "admin"
        and str(mat.created_by.id) != str(user.id)
    ):
        return jsonify({
            "error": "You can only update your own materials"
        }), 403

    data = request.get_json()
    for field in ["title", "url", "description"]:
        if field in data:
            setattr(mat, field, data[field])

    if "material_type" in data:
        if data["material_type"] not in MATERIAL_TYPES:
            return jsonify({
                "error": (
                    f"material_type must be one of {MATERIAL_TYPES}"
                )
            }), 400
        mat.material_type = data["material_type"]

    mat.save()
    return jsonify({
        "message": "Material updated",
        "material": mat.to_dict(),
    }), 200


# ── DELETE /materials/<id> ──────────────────────────────────────────────
@materials_bp.route("/<material_id>", methods=["DELETE"])
@jwt_required()
@role_required("organizer", "admin")
def delete_material(material_id):
    """
    Delete a material.
    ---
    tags: [Materials]
    security: [{Bearer: []}]
    """
    mat = get_object_or_404(
        SessionMaterial, id=material_id,
        description="Material not found",
    )
    user = get_current_user()

    if (
        user.role != "admin"
        and str(mat.created_by.id) != str(user.id)
    ):
        return jsonify({
            "error": "You can only delete your own materials"
        }), 403

    mat.delete()
    return jsonify({"message": "Material deleted"}), 200
