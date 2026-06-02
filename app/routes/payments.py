import hmac, hashlib
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
import razorpay
from app.models import Payment, Course, Event, Registration
from app.utils import get_current_user, get_object_or_404

payments_bp = Blueprint("payments", __name__)


def rzp():
    return razorpay.Client(auth=(current_app.config["RAZORPAY_KEY_ID"],
                                  current_app.config["RAZORPAY_KEY_SECRET"]))


@payments_bp.route("/create-order", methods=["POST"])
@jwt_required()
def create_order():
    """Create Payment Order --- tags: [Payments] security: [{Bearer: []}]"""
    data = request.get_json()
    user = get_current_user()
    payment_type = data.get("payment_type")
    item_id = data.get("item_id")
    if payment_type not in ("course", "event"):
        return jsonify({"error": "payment_type must be 'course' or 'event'"}), 400
    if not item_id:
        return jsonify({"error": "item_id is required"}), 400

    if payment_type == "course":
        item = Course.objects(id=item_id).first()
        if not item:
            return jsonify({"error": "Course not found"}), 404
    else:
        item = Event.objects(id=item_id).first()
        if not item:
            return jsonify({"error": "Event not found"}), 404
        if item.price == 0:
            return jsonify({"error": "This event is free. Use POST /events/<id>/register"}), 400

    amount_paise = int(item.price * 100)
    try:
        rz_order = rzp().order.create({
            "amount": amount_paise, "currency": "INR", "payment_capture": 1,
            "notes": {"user_id": str(user.id), "payment_type": payment_type, "item_id": str(item_id)}
        })
    except Exception as e:
        return jsonify({"error": "Razorpay order creation failed", "details": str(e)}), 502

    payment = Payment(
        user=user, razorpay_order_id=rz_order["id"],
        amount=item.price, currency="INR", status="created", payment_type=payment_type,
        course=item if payment_type == "course" else None,
        event=item if payment_type == "event" else None,
    )
    payment.save()
    return jsonify({"message": "Order created", "order_id": rz_order["id"],
                    "amount": item.price, "amount_paise": amount_paise, "currency": "INR",
                    "payment_id": str(payment.id)}), 201


@payments_bp.route("/verify", methods=["POST"])
@jwt_required()
def verify_payment():
    """Verify Payment --- tags: [Payments] security: [{Bearer: []}]"""
    data = request.get_json()
    user = get_current_user()
    for field in ["razorpay_order_id", "razorpay_payment_id", "razorpay_signature"]:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    payment = Payment.objects(razorpay_order_id=data["razorpay_order_id"], user=user).first()
    if not payment:
        return jsonify({"error": "Payment record not found"}), 404
    if payment.status == "paid":
        return jsonify({"message": "Payment already verified", "payment": payment.to_dict()}), 200

    payment.razorpay_payment_id = data["razorpay_payment_id"]
    payment.razorpay_signature = data["razorpay_signature"]
    payment.status = "paid"
    payment.paid_at = datetime.now(timezone.utc)
    payment.save()

    if payment.payment_type == "event" and payment.event:
        if not Registration.objects(user=user, event=payment.event).first():
            reg = Registration(user=user, event=payment.event, status="confirmed")
            reg.generate_qr_token()
            reg.save()

    return jsonify({"message": "Payment verified", "payment": payment.to_dict()}), 200


@payments_bp.route("/history", methods=["GET"])
@jwt_required()
def payment_history():
    """Payment History --- tags: [Payments] security: [{Bearer: []}]"""
    user = get_current_user()
    payments = Payment.objects(user=user).order_by("-created_at")
    return jsonify({"payments": [p.to_dict() for p in payments]}), 200