"""
SkillConnect – Event Routes
================================
Advanced event management system with:
- Event CRUD
- Event registration
- Capacity tracking
- Virtual events
- Event analytics
- Event ending & certificates
- Search & filtering
- Organizer dashboard
"""

from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required
)

from datetime import (
    datetime,
    timezone
)

from mongoengine.errors import (
    NotUniqueError
)

from app.models.event_model import Event
from app.models.registration_model import Registration
from app.models.certificate_model import Certificate

from app.utils.decorators import role_required

from app.utils.jwt_utils import (
    get_current_user,
    get_object_or_404
)

events_bp = Blueprint(
    "events",
    __name__
)

DATE_FMT = "%Y-%m-%d %H:%M"


# ═════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════

def parse_date(date_string):

    try:

        return datetime.strptime(
            date_string,
            DATE_FMT
        )

    except Exception:

        return None


# ═════════════════════════════════════════════════════════════
# CREATE EVENT
# ═════════════════════════════════════════════════════════════

@events_bp.route("", methods=["POST"])
@jwt_required()
@role_required("organizer", "admin")
def create_event():
    """
    Create new event
    ---
    tags:
      - Events
    security:
      - Bearer: []
    """

    data = request.get_json()

    required_fields = [
        "title",
        "description",
        "event_date"
    ]

    for field in required_fields:

        if not data.get(field):

            return jsonify({
                "error":
                    f"{field} is required"
            }), 400

    event_date = parse_date(
        data["event_date"]
    )

    if not event_date:

        return jsonify({
            "error":
                "event_date must be "
                "'YYYY-MM-DD HH:MM'"
        }), 400

    end_date = None

    if data.get("end_date"):

        end_date = parse_date(
            data["end_date"]
        )

    event_type = data.get(
        "event_type",
        "event"
    )

    if event_type not in (
        "event",
        "workshop"
    ):

        return jsonify({
            "error":
                "Invalid event type"
        }), 400

    user = get_current_user()

    event = Event(

        title=data["title"],

        description=data["description"],

        event_type=event_type,

        venue=data.get("venue"),

        event_date=event_date,

        end_date=end_date,

        price=float(
            data.get("price", 0)
        ),

        capacity=int(
            data.get("capacity", 100)
        ),

        tags=data.get("tags", []),

        category=data.get("category"),

        banner_url=data.get(
            "banner_url"
        ),

        is_virtual=bool(
            data.get(
                "is_virtual",
                False
            )
        ),

        meeting_link=data.get(
            "meeting_link"
        ),

        created_by=user,

        created_at=datetime.now(
            timezone.utc
        )

    )

    event.save()

    return jsonify({

        "message":
            "Event created successfully",

        "event":
            event.to_dict()

    }), 201


# ═════════════════════════════════════════════════════════════
# GET ALL EVENTS
# ═════════════════════════════════════════════════════════════

@events_bp.route("", methods=["GET"])
def get_all_events():
    """
    Get all events
    ---
    tags:
      - Events
    """

    event_type = request.args.get(
        "type"
    )

    search = request.args.get(
        "search",
        ""
    ).strip()

    category = request.args.get(
        "category"
    )

    query = Event.objects()

    if event_type:

        query = query.filter(
            event_type=event_type
        )

    if category:

        query = query.filter(
            category=category
        )

    if search:

        query = query.filter(

            __raw__={

                "$or": [

                    {
                        "title": {
                            "$regex": search,
                            "$options": "i"
                        }
                    },

                    {
                        "description": {
                            "$regex": search,
                            "$options": "i"
                        }
                    }

                ]
            }
        )

    events = query.order_by(
        "event_date"
    )

    return jsonify({

        "total":
            events.count(),

        "events": [
            event.to_dict()
            for event in events
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# GET SINGLE EVENT
# ═════════════════════════════════════════════════════════════

@events_bp.route(
    "/<event_id>",
    methods=["GET"]
)
def get_event(event_id):
    """
    Get event details
    ---
    tags:
      - Events
    """

    event = get_object_or_404(

        Event,

        id=event_id,

        description=
            "Event not found"

    )

    return jsonify({
        "event":
            event.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# UPDATE EVENT
# ═════════════════════════════════════════════════════════════

@events_bp.route(
    "/<event_id>",
    methods=["PUT"]
)
@jwt_required()
@role_required("organizer", "admin")
def update_event(event_id):
    """
    Update event
    ---
    tags:
      - Events
    security:
      - Bearer: []
    """

    event = get_object_or_404(

        Event,

        id=event_id,

        description=
            "Event not found"

    )

    user = get_current_user()

    if (

        user.role != "admin"

        and

        str(event.created_by.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "You can only update "
                "your own events"
        }), 403

    data = request.get_json()

    editable_fields = [

        "title",

        "description",

        "venue",

        "event_type",

        "meeting_link",

        "banner_url",

        "category"

    ]

    for field in editable_fields:

        if field in data:

            setattr(
                event,
                field,
                data[field]
            )

    if "price" in data:

        event.price = float(
            data["price"]
        )

    if "capacity" in data:

        event.capacity = int(
            data["capacity"]
        )

    if "tags" in data:

        event.tags = data["tags"]

    if "is_virtual" in data:

        event.is_virtual = bool(
            data["is_virtual"]
        )

    if "event_date" in data:

        parsed = parse_date(
            data["event_date"]
        )

        if not parsed:

            return jsonify({
                "error":
                    "Invalid event_date format"
            }), 400

        event.event_date = parsed

    if "end_date" in data:

        parsed = parse_date(
            data["end_date"]
        )

        if parsed:

            event.end_date = parsed

    event.updated_at = datetime.now(
        timezone.utc
    )

    event.save()

    return jsonify({

        "message":
            "Event updated successfully",

        "event":
            event.to_dict()

    }), 200


# ═════════════════════════════════════════════════════════════
# DELETE EVENT
# ═════════════════════════════════════════════════════════════

@events_bp.route(
    "/<event_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_event(event_id):
    """
    Delete event
    ---
    tags:
      - Events
    security:
      - Bearer: []
    """

    user = get_current_user()

    event = get_object_or_404(

        Event,

        id=event_id,

        description=
            "Event not found"

    )

    if (

        str(event.created_by.id)
        != str(user.id)

        and

        user.role != "admin"

    ):

        return jsonify({
            "error":
                "Unauthorized"
        }), 403

    deleted_regs = Registration.objects(
        event=event
    ).count()

    Registration.objects(
        event=event
    ).delete()

    title = event.title

    event.delete()

    return jsonify({

        "message":
            f'Event "{title}" deleted',

        "registrations_removed":
            deleted_regs

    }), 200


# ═════════════════════════════════════════════════════════════
# REGISTER EVENT
# ═════════════════════════════════════════════════════════════

@events_bp.route(
    "/<event_id>/register",
    methods=["POST"]
)
@jwt_required()
def register_event(event_id):
    """
    Register for event
    ---
    tags:
      - Event Registration
    security:
      - Bearer: []
    """

    event = get_object_or_404(

        Event,

        id=event_id,

        description=
            "Event not found"

    )

    user = get_current_user()

    existing = Registration.objects(
        user=user,
        event=event
    ).first()

    if existing:

        return jsonify({
            "error":
                "Already registered"
        }), 409

    confirmed = Registration.objects(

        event=event,

        status="confirmed"

    ).count()

    if confirmed >= event.capacity:

        return jsonify({
            "error":
                "Event full"
        }), 400

    registration = Registration(

        user=user,

        event=event,

        status="confirmed"

    )

    registration.generate_qr_token()

    registration.save()

    return jsonify({

        "message":
            "Registration successful",

        "registration":
            registration.to_dict()

    }), 201


# ═════════════════════════════════════════════════════════════
# MY REGISTRATIONS
# ═════════════════════════════════════════════════════════════

@events_bp.route(
    "/my-registrations",
    methods=["GET"]
)
@jwt_required()
def my_registrations():
    """
    Get my registrations
    ---
    tags:
      - Event Registration
    security:
      - Bearer: []
    """

    user = get_current_user()

    registrations = Registration.objects(
        user=user
    ).order_by("-registered_at")

    return jsonify({

        "total":
            registrations.count(),

        "registrations": [
            reg.to_dict()
            for reg in registrations
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# EVENT REGISTRATIONS
# ═════════════════════════════════════════════════════════════

@events_bp.route(
    "/<event_id>/registrations",
    methods=["GET"]
)
@jwt_required()
@role_required("organizer", "admin")
def event_registrations(event_id):
    """
    Get event registrations
    ---
    tags:
      - Event Registration
    security:
      - Bearer: []
    """

    user = get_current_user()

    event = get_object_or_404(

        Event,

        id=event_id,

        description=
            "Event not found"

    )

    if (

        user.role != "admin"

        and

        str(event.created_by.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "Access denied"
        }), 403

    registrations = Registration.objects(
        event=event
    ).order_by("-registered_at")

    return jsonify({

        "total":
            registrations.count(),

        "registrations": [
            reg.to_dict()
            for reg in registrations
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# END EVENT
# ═════════════════════════════════════════════════════════════

@events_bp.route(
    "/<event_id>/end",
    methods=["POST"]
)
@jwt_required()
@role_required("organizer", "admin")
def end_event(event_id):
    """
    End event & issue certificates
    ---
    tags:
      - Events
    security:
      - Bearer: []
    """

    user = get_current_user()

    event = get_object_or_404(

        Event,

        id=event_id,

        description=
            "Event not found"

    )

    if (

        user.role != "admin"

        and

        str(event.created_by.id)
        != str(user.id)

    ):

        return jsonify({
            "error":
                "You can only end "
                "your own events"
        }), 403

    if event.is_ended:

        return jsonify({
            "error":
                "Event already ended"
        }), 409

    event.is_ended = True

    event.ended_at = datetime.now(
        timezone.utc
    )

    event.save()

    event_date_str = ""

    try:

        if event.event_date:

            event_date_str = (
                event.event_date.strftime(
                    "%d %b %Y"
                )
            )

    except Exception:

        event_date_str = str(
            event.event_date
        )[:10]

    registrations = Registration.objects(

        event=event,

        status="confirmed"

    )

    issued = 0
    skipped = 0

    for reg in registrations:

        try:

            attendee = reg.user

            certificate = Certificate(

                certificate_id=
                    Certificate.generate_id(),

                recipient=attendee,

                event=event,

                issued_by=user,

                recipient_name=
                    attendee.name,

                event_title=
                    event.title,

                organizer_name=
                    user.name,

                event_date=
                    event_date_str,

            )

            certificate.save()

            issued += 1

        except NotUniqueError:

            skipped += 1

        except Exception:

            skipped += 1

    return jsonify({

        "message":
            f'Event "{event.title}" ended',

        "certificates_issued":
            issued,

        "certificates_skipped":
            skipped,

        "event":
            event.to_dict()

    }), 200


# ═════════════════════════════════════════════════════════════
# FEATURED EVENTS
# ═════════════════════════════════════════════════════════════

@events_bp.route(
    "/featured",
    methods=["GET"]
)
def featured_events():
    """
    Featured events
    ---
    tags:
      - Events
    """

    events = Event.objects.order_by(
        "-created_at"
    )[:6]

    return jsonify({

        "events": [
            event.to_dict()
            for event in events
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# EVENT ANALYTICS
# ═════════════════════════════════════════════════════════════

@events_bp.route(
    "/analytics/overview",
    methods=["GET"]
)
@jwt_required()
@role_required("admin")
def analytics_overview():
    """
    Event analytics
    ---
    tags:
      - Event Analytics
    security:
      - Bearer: []
    """

    total_events = Event.objects.count()

    virtual_events = Event.objects(
        is_virtual=True
    ).count()

    physical_events = Event.objects(
        is_virtual=False
    ).count()

    ended_events = Event.objects(
        is_ended=True
    ).count()

    total_registrations = (
        Registration.objects.count()
    )

    return jsonify({

        "total_events":
            total_events,

        "virtual_events":
            virtual_events,

        "physical_events":
            physical_events,

        "ended_events":
            ended_events,

        "total_registrations":
            total_registrations,

    }), 200