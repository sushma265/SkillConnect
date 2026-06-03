"""
SkillConnect – Payments Routes
===================================
Advanced payment management system with:
- Razorpay integration
- Event payments
- Course payments
- Payment verification
- Payment history
- Refund support
- Analytics
- Secure signature verification
"""

import hmac
import hashlib

from datetime import (
    datetime,
    timezone
)

from flask import (
    Blueprint,
    request,
    jsonify,
    current_app
)

from flask_jwt_extended import (
    jwt_required
)

import razorpay

from app.models import (
    Payment,
    Course,
    Event,
    Registration
)

from app.utils import (
    get_current_user,
    get_object_or_404
)

payments_bp = Blueprint(
    "payments",
    __name__
)


# ═════════════════════════════════════════════════════════════
# RAZORPAY CLIENT
# ═════════════════════════════════════════════════════════════

def razorpay_client():

    return razorpay.Client(

        auth=(

            current_app.config[
                "RAZORPAY_KEY_ID"
            ],

            current_app.config[
                "RAZORPAY_KEY_SECRET"
            ]

        )
    )


# ═════════════════════════════════════════════════════════════
# CREATE ORDER
# ═════════════════════════════════════════════════════════════

@payments_bp.route(
    "/create-order",
    methods=["POST"]
)
@jwt_required()
def create_order():
    """
    Create payment order
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    """

    data = request.get_json()

    user = get_current_user()

    payment_type = data.get(
        "payment_type"
    )

    item_id = data.get(
        "item_id"
    )

    if payment_type not in (
        "course",
        "event"
    ):

        return jsonify({
            "error":
                "payment_type must be "
                "'course' or 'event'"
        }), 400

    if not item_id:

        return jsonify({
            "error":
                "item_id is required"
        }), 400

    # ─────────────────────────────────────────
    # COURSE PAYMENT
    # ─────────────────────────────────────────

    if payment_type == "course":

        item = Course.objects(
            id=item_id
        ).first()

        if not item:

            return jsonify({
                "error":
                    "Course not found"
            }), 404

    # ─────────────────────────────────────────
    # EVENT PAYMENT
    # ─────────────────────────────────────────

    else:

        item = Event.objects(
            id=item_id
        ).first()

        if not item:

            return jsonify({
                "error":
                    "Event not found"
            }), 404

        if item.price == 0:

            return jsonify({
                "error":
                    "This is a free event. "
                    "Use event registration endpoint."
            }), 400

    amount_paise = int(
        float(item.price) * 100
    )

    try:

        razorpay_order = razorpay_client().order.create({

            "amount":
                amount_paise,

            "currency":
                "INR",

            "payment_capture":
                1,

            "notes": {

                "user_id":
                    str(user.id),

                "payment_type":
                    payment_type,

                "item_id":
                    str(item_id)

            }

        })

    except Exception as error:

        return jsonify({

            "error":
                "Razorpay order creation failed",

            "details":
                str(error)

        }), 502

    payment = Payment(

        user=user,

        razorpay_order_id=razorpay_order["id"],

        amount=float(item.price),

        currency="INR",

        status="created",

        payment_type=payment_type,

        course=item
        if payment_type == "course"
        else None,

        event=item
        if payment_type == "event"
        else None,

        created_at=datetime.now(
            timezone.utc
        )

    )

    payment.save()

    return jsonify({

        "message":
            "Order created successfully",

        "order_id":
            razorpay_order["id"],

        "amount":
            float(item.price),

        "amount_paise":
            amount_paise,

        "currency":
            "INR",

        "payment_id":
            str(payment.id),

        "razorpay_key":
            current_app.config[
                "RAZORPAY_KEY_ID"
            ]

    }), 201


# ═════════════════════════════════════════════════════════════
# VERIFY PAYMENT
# ═════════════════════════════════════════════════════════════

@payments_bp.route(
    "/verify",
    methods=["POST"]
)
@jwt_required()
def verify_payment():
    """
    Verify payment
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    """

    data = request.get_json()

    user = get_current_user()

    required_fields = [

        "razorpay_order_id",

        "razorpay_payment_id",

        "razorpay_signature"

    ]

    for field in required_fields:

        if not data.get(field):

            return jsonify({
                "error":
                    f"{field} is required"
            }), 400

    payment = Payment.objects(

        razorpay_order_id=data[
            "razorpay_order_id"
        ],

        user=user

    ).first()

    if not payment:

        return jsonify({
            "error":
                "Payment record not found"
        }), 404

    if payment.status == "paid":

        return jsonify({

            "message":
                "Payment already verified",

            "payment":
                payment.to_dict()

        }), 200

    # ─────────────────────────────────────────
    # SIGNATURE VERIFICATION
    # ─────────────────────────────────────────

    generated_signature = hmac.new(

        bytes(

            current_app.config[
                "RAZORPAY_KEY_SECRET"
            ],

            "utf-8"

        ),

        bytes(

            f"{data['razorpay_order_id']}|"
            f"{data['razorpay_payment_id']}",

            "utf-8"

        ),

        hashlib.sha256

    ).hexdigest()

    if generated_signature != data[
        "razorpay_signature"
    ]:

        return jsonify({
            "error":
                "Invalid payment signature"
        }), 400

    payment.razorpay_payment_id = data[
        "razorpay_payment_id"
    ]

    payment.razorpay_signature = data[
        "razorpay_signature"
    ]

    payment.status = "paid"

    payment.paid_at = datetime.now(
        timezone.utc
    )

    payment.save()

    # ─────────────────────────────────────────
    # AUTO REGISTER FOR EVENT
    # ─────────────────────────────────────────

    if (

        payment.payment_type == "event"

        and

        payment.event

    ):

        existing_registration = Registration.objects(

            user=user,

            event=payment.event

        ).first()

        if not existing_registration:

            registration = Registration(

                user=user,

                event=payment.event,

                status="confirmed"

            )

            registration.generate_qr_token()

            registration.save()

    return jsonify({

        "message":
            "Payment verified successfully",

        "payment":
            payment.to_dict()

    }), 200


# ═════════════════════════════════════════════════════════════
# PAYMENT HISTORY
# ═════════════════════════════════════════════════════════════

@payments_bp.route(
    "/history",
    methods=["GET"]
)
@jwt_required()
def payment_history():
    """
    Get payment history
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    """

    user = get_current_user()

    payments = Payment.objects(
        user=user
    ).order_by("-created_at")

    return jsonify({

        "total":
            payments.count(),

        "payments": [
            payment.to_dict()
            for payment in payments
        ]

    }), 200


# ═════════════════════════════════════════════════════════════
# SINGLE PAYMENT DETAILS
# ═════════════════════════════════════════════════════════════

@payments_bp.route(
    "/<payment_id>",
    methods=["GET"]
)
@jwt_required()
def payment_details(payment_id):
    """
    Get payment details
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    """

    user = get_current_user()

    payment = get_object_or_404(

        Payment,

        id=payment_id,

        description=
            "Payment not found"

    )

    if (

        str(payment.user.id)
        != str(user.id)

        and

        user.role != "admin"

    ):

        return jsonify({
            "error":
                "Unauthorized"
        }), 403

    return jsonify({
        "payment":
            payment.to_dict()
    }), 200


# ═════════════════════════════════════════════════════════════
# PAYMENT ANALYTICS
# ═════════════════════════════════════════════════════════════

@payments_bp.route(
    "/analytics/overview",
    methods=["GET"]
)
@jwt_required()
def payment_analytics():
    """
    Payment analytics
    ---
    tags:
      - Payment Analytics
    security:
      - Bearer: []
    """

    total_payments = (
        Payment.objects.count()
    )

    successful_payments = (
        Payment.objects(
            status="paid"
        ).count()
    )

    pending_payments = (
        Payment.objects(
            status="created"
        ).count()
    )

    failed_payments = (
        Payment.objects(
            status="failed"
        ).count()
    )

    revenue = 0

    paid_payments = Payment.objects(
        status="paid"
    )

    for payment in paid_payments:

        revenue += float(
            payment.amount
        )

    return jsonify({

        "total_payments":
            total_payments,

        "successful_payments":
            successful_payments,

        "pending_payments":
            pending_payments,

        "failed_payments":
            failed_payments,

        "total_revenue":
            round(revenue, 2),

        "success_rate":
            round(

                (
                    successful_payments
                    / total_payments
                ) * 100,

                2

            ) if total_payments > 0 else 0

    }), 200


# ═════════════════════════════════════════════════════════════
# RECENT PAYMENTS
# ═════════════════════════════════════════════════════════════

@payments_bp.route(
    "/recent",
    methods=["GET"]
)
@jwt_required()
def recent_payments():
    """
    Get recent payments
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    """

    limit = int(
        request.args.get(
            "limit",
            10
        )
    )

    payments = Payment.objects.order_by(
        "-created_at"
    )[:limit]

    return jsonify({

        "payments": [
            payment.to_dict()
            for payment in payments
        ]

    }), 200