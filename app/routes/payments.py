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
    return razorpay.Client(auth=(key_id, key_secret))


# ── POST /payments/create-order ───────────────────────────────────────────
@payments_bp.route("/create-order", methods=["POST"])
@jwt_required()
def create_order():
    """
    Creates a Razorpay order for a course purchase or event registration.

    Body:
        payment_type : "course" | "event"
        item_id      : ID of the course or event
    """
    data = request.get_json()
    user = get_current_user()

    payment_type = data.get("payment_type")
    item_id = data.get("item_id")

    if payment_type not in ("course", "event"):
        return jsonify({"error": "payment_type must be 'course' or 'event'"}), 400
    if not item_id:
        return jsonify({"error": "'item_id' is required"}), 400

    # Resolve amount
    if payment_type == "course":
        item = Course.query.get(item_id)
        if not item:
            return jsonify({"error": "Course not found"}), 404
        amount = item.price
    else:
        item = Event.query.get(item_id)
        if not item:
            return jsonify({"error": "Event not found"}), 404
        if item.price == 0:
            return jsonify({"error": "This event is free. Use POST /events/<id>/register"}), 400
        amount = item.price

    # Razorpay expects amount in paise (1 INR = 100 paise)
    amount_paise = int(amount * 100)

    client = get_razorpay_client()
    try:
        rz_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "user_id": str(user.id),
                "payment_type": payment_type,
                "item_id": str(item_id),
            }
        })
    except Exception as e:
        return jsonify({"error": "Razorpay order creation failed", "details": str(e)}), 502

    # Save order to DB
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
        "message": "Order created. Complete payment using the Razorpay SDK.",
        "order_id": rz_order["id"],
        "amount": amount,
        "amount_paise": amount_paise,
        "currency": "INR",
        "razorpay_key_id": current_app.config["RAZORPAY_KEY_ID"],
        "payment_id": payment.id,
    }), 201


# ── POST /payments/verify ─────────────────────────────────────────────────
@payments_bp.route("/verify", methods=["POST"])
@jwt_required()
def verify_payment():
    """
    Verify Razorpay payment signature after frontend completes checkout.

    Body:
        razorpay_order_id   : from create-order response
        razorpay_payment_id : from Razorpay checkout callback
        razorpay_signature  : from Razorpay checkout callback
    """
    data = request.get_json()
    user = get_current_user()

    required = ["razorpay_order_id", "razorpay_payment_id", "razorpay_signature"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    payment = Payment.query.filter_by(
        razorpay_order_id=data["razorpay_order_id"],
        user_id=user.id,
    ).first()

    if not payment:
        return jsonify({"error": "Payment record not found"}), 404

    if payment.status == "paid":
        return jsonify({"message": "Payment already verified", "payment": payment.to_dict()}), 200

    # Signature verification
    key_secret = current_app.config["RAZORPAY_KEY_SECRET"]
    msg = f"{data['razorpay_order_id']}|{data['razorpay_payment_id']}"
    expected_signature = hmac.new(
        key_secret.encode(), msg.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, data["razorpay_signature"]):
        payment.status = "failed"
        db.session.commit()
        return jsonify({"error": "Payment verification failed – invalid signature"}), 400

    # Mark payment as paid
    payment.razorpay_payment_id = data["razorpay_payment_id"]
    payment.razorpay_signature = data["razorpay_signature"]
    payment.status = "paid"
    payment.paid_at = datetime.now(timezone.utc)
    db.session.commit()

    # Post-payment actions
    if payment.payment_type == "event" and payment.event_id:
        existing = Registration.query.filter_by(
            user_id=user.id, event_id=payment.event_id
        ).first()
        if not existing:
            reg = Registration(
                user_id=user.id,
                event_id=payment.event_id,
                status="confirmed",
            )
            db.session.add(reg)
            db.session.commit()

    return jsonify({
        "message": "Payment verified successfully",
        "payment": payment.to_dict()
    }), 200


# ── GET /payments/history ─────────────────────────────────────────────────
@payments_bp.route("/history", methods=["GET"])
@jwt_required()
def payment_history():
    user = get_current_user()
    payments = (
        Payment.query
        .filter_by(user_id=user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    return jsonify({"payments": [p.to_dict() for p in payments]}), 200
