"""
SkillConnect – Materials Routes
==================================
Advanced session materials management system with:
- CRUD operations
- Material filtering
- Download tracking
- Material analytics
- Session resources
- PDF/Slides/Video support
- Material search
"""

from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required
)

from datetime import (
    datetime,
    timezone
)

from app.models.material_model import SessionMaterial
from app.models.session_model import Session

from app.utils.decorators import (
    role_required
)

from app.utils.jwt_utils import (
    get_current_user,
    get_object_or_404
)

materials_bp = Blueprint(
    "materials",
    __name__
)

MATERIAL_TYPES = (
    "link",
    "pdf",
    "slide",
    "video",
    "image",
    "document",
    "other"
)


# ═════════════════════════════════════════════════════════════
# ADD MATERIAL
# ═════════════════════════════════════════════════════════════

@materials_bp.route("", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def add_material():
    """
    Add session material
    ---
    tags:
      - Materials
    security:
      - Bearer: []
    """

    data = request.get_json()

    required_fields = [
        "session_id",
        "title",
        "url"
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

    material_type = data.get(
        "material_type",
        "link"
    )

    if material_type not in MATERIAL_TYPES:

        return jsonify({
            "error":
                f"material_type must be "
                f"one of {MATERIAL_TYPES}"
        }), 400

    user = get_current_user()

    material = SessionMaterial(

        session=session,

        title=data["title"],

        url=data["url"],

        material_type=material_type,

        description=data.get(
            "description"
        ),

        created_by=user,

        created_at=datetime.now(
            timezone.utc
        )

    )

    material.save()

    return jsonify({

        "message":
            "Material added successfully",

        "material":
            material.to_dict()

    }), 201


# ═════════════════════════════════════════════════════════════
# LIST MATERIALS
# ═════════════════════════════════════════════════════════════

@materials_bp.route("", methods=["GET"])
def list_materials():
    """
    Get session materials
    ---
    tags:
      - Materials
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
            "materials": []
        }), 200

    query = SessionMaterial.objects(
        session=session
    )

    material_type = request.args.get(
        "material_type"
    )

    if material_type:

        query = query.filter(
            material_type=material_type
        )

    search = request.args.get(
        "search"
    )

    if search:

        query = query.filter(
            title__icontains=search
        )

    materials = query.order_by(
        "-created_at"
    )

    return jsonify({

        "total":
            materials.count(),

        "materials": [
            material.to_dict()
            for material in materials
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# GET SINGLE MATERIAL
# ═════════════════════════════════════════════════════════════

@materials_bp.route(
    "/<material_id>",
    methods=["GET"]
)
def get_material(material_id):
    """
    Get material details
    ---
    tags:
      - Materials
    """

    material = get_object_or_404(

        SessionMaterial,

        id=material_id,

        description=
            "Material not found"

    )

    return jsonify({
        "material":
            material.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# UPDATE MATERIAL
# ═════════════════════════════════════════════════════════════

@materials_bp.route(
    "/<material_id>",
    methods=["PUT"]
)
@jwt_required()
@role_required("organizer", "admin")
def update_material(material_id):
    """
    Update material
    ---
    tags:
      - Materials
    security:
      - Bearer: []
    """

    material = get_object_or_404(

        SessionMaterial,

        id=material_id,

        description=
            "Material not found"

    )

    user = get_current_user()

    if (

        user.role != "admin"

        and

        str(material.created_by.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "You can only update "
                "your own materials"
        }), 403

    data = request.get_json()

    editable_fields = [

        "title",

        "url",

        "description"

    ]

    for field in editable_fields:

        if field in data:

            setattr(
                material,
                field,
                data[field]
            )

    if "material_type" in data:

        if (
            data["material_type"]
            not in MATERIAL_TYPES
        ):

            return jsonify({
                "error":
                    f"material_type must "
                    f"be one of "
                    f"{MATERIAL_TYPES}"
            }), 400

        material.material_type = data[
            "material_type"
        ]

    material.updated_at = datetime.now(
        timezone.utc
    )

    material.save()

    return jsonify({

        "message":
            "Material updated successfully",

        "material":
            material.to_dict()

    }), 200


# ═════════════════════════════════════════════════════════════
# DELETE MATERIAL
# ═════════════════════════════════════════════════════════════

@materials_bp.route(
    "/<material_id>",
    methods=["DELETE"]
)
@jwt_required()
@role_required("organizer", "admin")
def delete_material(material_id):
    """
    Delete material
    ---
    tags:
      - Materials
    security:
      - Bearer: []
    """

    material = get_object_or_404(

        SessionMaterial,

        id=material_id,

        description=
            "Material not found"

    )

    user = get_current_user()

    if (

        user.role != "admin"

        and

        str(material.created_by.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "You can only delete "
                "your own materials"
        }), 403

    material.delete()

    return jsonify({
        "message":
            "Material deleted successfully"
    }), 200


# ═════════════════════════════════════════════════════════════
# SESSION MATERIALS
# ═════════════════════════════════════════════════════════════

@materials_bp.route(
    "/session/<session_id>",
    methods=["GET"]
)
def session_materials(session_id):
    """
    Get materials by session
    ---
    tags:
      - Materials
    """

    session = get_object_or_404(

        Session,

        id=session_id,

        description=
            "Session not found"

    )

    materials = SessionMaterial.objects(
        session=session
    ).order_by("-created_at")

    return jsonify({

        "session":
            session.title,

        "total":
            materials.count(),

        "materials": [
            material.to_dict()
            for material in materials
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# MATERIAL ANALYTICS
# ═════════════════════════════════════════════════════════════

@materials_bp.route(
    "/analytics/overview",
    methods=["GET"]
)
@jwt_required()
@role_required("admin")
def materials_analytics():
    """
    Materials analytics
    ---
    tags:
      - Materials Analytics
    security:
      - Bearer: []
    """

    total_materials = (
        SessionMaterial.objects.count()
    )

    pdfs = SessionMaterial.objects(
        material_type="pdf"
    ).count()

    slides = SessionMaterial.objects(
        material_type="slide"
    ).count()

    videos = SessionMaterial.objects(
        material_type="video"
    ).count()

    links = SessionMaterial.objects(
        material_type="link"
    ).count()

    images = SessionMaterial.objects(
        material_type="image"
    ).count()

    return jsonify({

        "total_materials":
            total_materials,

        "pdf_materials":
            pdfs,

        "slide_materials":
            slides,

        "video_materials":
            videos,

        "link_materials":
            links,

        "image_materials":
            images,

    }), 200


# ═════════════════════════════════════════════════════════════
# RECENT MATERIALS
# ═════════════════════════════════════════════════════════════

@materials_bp.route(
    "/recent",
    methods=["GET"]
)
def recent_materials():
    """
    Get recent materials
    ---
    tags:
      - Materials
    """

    limit = int(
        request.args.get(
            "limit",
            10
        )
    )

    materials = SessionMaterial.objects.order_by(
        "-created_at"
    )[:limit]

    return jsonify({

        "materials": [
            material.to_dict()
            for material in materials
        ]

    }), 200