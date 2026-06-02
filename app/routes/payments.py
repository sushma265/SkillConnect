import hmac
import hashlib
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

import razorpay

from app import db
from app.models import Payment, Course, Event, Registration
from app.utils import get_current_user

payments_bp = Blueprint("payments", __name__)


def get_razorpay_client():
    key_id = current_app.config["RAZORPAY_KEY_ID"]
    key_secret = current_app.config["RAZORPAY_KEY_SECRET"]

    return razorpay.Client(
        auth=(key_id, key_secret)
    )


@payments_bp.route("/create-order", methods=["POST"])
@jwt_required()
def create_order():
    """
    Create Payment Order API
    ---
    tags:
      - Payments

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
            - payment_type
            - item_id

          properties:
            payment_type:
              type: string
              example: course

            item_id:
              type: integer
              example: 1

    responses:
      201:
        description: Razorpay order created successfully

      400:
        description: Invalid request

      401:
        description: Unauthorized

      404:
        description: Course or Event not found
    """

    data = request.get_json()

    user = get_current_user()

    payment_type = data.get("payment_type")
    item_id = data.get("item_id")

    if payment_type not in ("course", "event"):
        return jsonify({
            "error": "payment_type must be 'course' or 'event'"
        }), 400

    if not item_id:
        return jsonify({
            "error": "item_id is required"
        }), 400

    if payment_type == "course":

        item = Course.query.get(item_id)

        if not item:
            return jsonify({
                "error": "Course not found"
            }), 404

        amount = item.price

    else:

        item = Event.query.get(item_id)

        if not item:
            return jsonify({
                "error": "Event not found"
            }), 404

        if item.price == 0:
            return jsonify({
                "error": "This event is free. Use POST /events/<id>/register"
            }), 400

        amount = item.price

    amount_paise = int(amount * 100)

    try:

        client = get_razorpay_client()

        rz_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "user_id": str(user.id),
                "payment_type": payment_type,
                "item_id": str(item_id)
            }
        })

    except Exception as e:

        return jsonify({
            "error": "Razorpay order creation failed",
            "details": str(e)
        }), 502

    payment = Payment(
        user_id=user.id,
        razorpay_order_id=rz_order["id"],
        amount=amount,
        currency="INR",
        status="created",
        payment_type=payment_type,
        course_id=item_id if payment_type == "course" else None,
        event_id=item_id if payment_type == "event" else None,
    )

    db.session.add(payment)
    db.session.commit()

    return jsonify({
        "message": "Order created successfully",
        "order_id": rz_order["id"],
        "amount": amount,
        "amount_paise": amount_paise,
        "currency": "INR",
        "payment_id": payment.id
    }), 201


@payments_bp.route("/verify", methods=["POST"])
@jwt_required()
def verify_payment():
    """
    Verify Payment API
    ---
    tags:
      - Payments

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
            - razorpay_order_id
            - razorpay_payment_id
            - razorpay_signature

          properties:
            razorpay_order_id:
              type: string
              example: order_Q12345

            razorpay_payment_id:
              type: string
              example: pay_Q12345

            razorpay_signature:
              type: string
              example: abc123signature

    responses:
      200:
        description: Payment verified successfully

      400:
        description: Missing required fields

      401:
        description: Unauthorized

      404:
        description: Payment not found
    """

    data = request.get_json()

    user = get_current_user()

    required = [
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature"
    ]

    for field in required:
        if not data.get(field):
            return jsonify({
                "error": f"{field} is required"
            }), 400

    payment = Payment.query.filter_by(
        razorpay_order_id=data["razorpay_order_id"],
        user_id=user.id
    ).first()

    if not payment:
        return jsonify({
            "error": "Payment record not found"
        }), 404

    if payment.status == "paid":
        return jsonify({
            "message": "Payment already verified",
            "payment": payment.to_dict()
        }), 200

    payment.razorpay_payment_id = data["razorpay_payment_id"]

    payment.razorpay_signature = data["razorpay_signature"]

    payment.status = "paid"

    payment.paid_at = datetime.now(timezone.utc)

    db.session.commit()

    if payment.payment_type == "event" and payment.event_id:

        existing = Registration.query.filter_by(
            user_id=user.id,
            event_id=payment.event_id
        ).first()

        if not existing:

            reg = Registration(
                user_id=user.id,
                event_id=payment.event_id,
                status="confirmed"
            )

            db.session.add(reg)
            db.session.commit()

    return jsonify({
        "message": "Payment verified successfully",
        "payment": payment.to_dict()
    }), 200


@payments_bp.route("/history", methods=["GET"])
@jwt_required()
def payment_history():
    """
    Payment History API
    ---
    tags:
      - Payments

    security:
      - Bearer: []

    responses:
      200:
        description: User payment history returned
    """

    user = get_current_user()

    payments = (
        Payment.query
        .filter_by(user_id=user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    return jsonify({
        "payments": [p.to_dict() for p in payments]
    }), 200