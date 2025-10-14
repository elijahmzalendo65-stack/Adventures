# app/routes/booking.py

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone
from ..extensions import db
from ..models.booking import Booking
from ..models.adventure import Adventure
from ..models.payment import Payment
from ..utils.helpers import login_required
from ..utils.mpesa_utils import initiate_stk_push  # Optional for real payments

booking_bp = Blueprint("booking", __name__, url_prefix="/api/bookings")


# -----------------------------
# Create Booking
# -----------------------------
@booking_bp.route("/", methods=["POST"])
@login_required
def create_booking():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"message": "Unauthorized"}), 401

        data = request.get_json() or {}
        adventure_id = data.get("adventure_id")
        adventure_date_str = data.get("adventure_date")
        number_of_people = data.get("number_of_people")
        customer_name = data.get("customer_name", "Anonymous")
        customer_email = data.get("customer_email", "")
        customer_phone = data.get("customer_phone", "")
        special_requests = data.get("special_requests", "")

        # Validate required fields
        if not all([adventure_id, adventure_date_str, number_of_people]):
            return jsonify({
                "message": "adventure_id, adventure_date, and number_of_people are required"
            }), 400

        # Validate adventure exists and is active
        adventure = Adventure.query.filter_by(id=adventure_id, is_active=True).first()
        if not adventure:
            return jsonify({"message": "Adventure not found or inactive"}), 404

        # Validate and parse date (make it timezone-aware UTC)
        try:
            adventure_date = datetime.fromisoformat(adventure_date_str.replace("Z", "+00:00"))
            adventure_date = adventure_date.astimezone(timezone.utc)
            now_utc = datetime.now(timezone.utc)
            if adventure_date < now_utc:
                return jsonify({"message": "Adventure date must be in the future"}), 400
        except ValueError:
            return jsonify({"message": "Invalid date format. Use ISO 8601"}), 400

        # Validate number_of_people
        try:
            number_of_people = int(number_of_people)
            if number_of_people < 1:
                return jsonify({"message": "Number of people must be at least 1"}), 400
        except (ValueError, TypeError):
            return jsonify({"message": "Invalid number_of_people"}), 400

        # Check availability for the selected date
        confirmed_count = Booking.query.filter(
            Booking.adventure_id == adventure.id,
            db.func.date(Booking.adventure_date) == adventure_date.date(),
            Booking.status == "confirmed"
        ).count()
        available_slots = adventure.max_capacity - confirmed_count
        if number_of_people > available_slots:
            return jsonify({
                "message": f"Only {available_slots} slots available",
                "available_slots": available_slots
            }), 400

        # Create booking
        booking = Booking(
            user_id=user_id,
            adventure_id=adventure.id,
            adventure_date=adventure_date,
            number_of_people=number_of_people,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            special_requests=special_requests,
            total_amount=(adventure.price or 0) * number_of_people,
            status="pending"
        )

        db.session.add(booking)
        db.session.commit()
        db.session.refresh(booking)

        return jsonify({
            "message": "Booking created successfully",
            "booking": booking.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print("Booking creation error:", str(e))
        return jsonify({"message": "Failed to create booking", "error": str(e)}), 500


# -----------------------------
# Initiate M-Pesa Payment
# -----------------------------
@booking_bp.route("/initiate-payment", methods=["POST"])
@login_required
def initiate_payment():
    try:
        user_id = session.get("user_id")
        data = request.get_json() or {}
        booking_id = data.get("booking_id")
        phone_number = data.get("phone_number")

        if not booking_id or not phone_number:
            return jsonify({"message": "Booking ID and phone number are required"}), 400

        booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first()
        if not booking:
            return jsonify({"message": "Booking not found"}), 404
        if booking.status != "pending":
            return jsonify({"message": "Booking already paid or cancelled"}), 400

        # Optional: integrate with real M-Pesa STK push
        # response = initiate_stk_push(phone_number, booking.total_amount, f"BOOKING_{booking.id}", f"Payment for booking {booking.id}")
        response = {"CheckoutRequestID": f"MOCK_{booking.id}"}  # Mock for testing

        # Save payment record
        payment = Payment(
            user_id=user_id,
            adventure_id=booking.adventure_id,
            phone_number=phone_number,
            amount=booking.total_amount,
            checkout_request_id=response["CheckoutRequestID"],
            status="pending"
        )
        db.session.add(payment)
        db.session.flush()  # Assign payment.id
        booking.payment_id = payment.id
        db.session.commit()
        db.session.refresh(booking)

        return jsonify({
            "message": "Payment initiated successfully",
            "booking_id": booking.id,
            "payment_id": payment.id,
            "checkout_request_id": response["CheckoutRequestID"]
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Payment initiation error:", str(e))
        return jsonify({"message": "Failed to initiate payment", "error": str(e)}), 500


# -----------------------------
# Cancel Booking
# -----------------------------
@booking_bp.route("/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    try:
        user_id = session.get("user_id")
        booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first()
        if not booking:
            return jsonify({"message": "Booking not found"}), 404

        if booking.status not in ["pending", "confirmed"]:
            return jsonify({"message": "Cannot cancel this booking"}), 400

        booking.status = "cancelled"
        db.session.commit()
        db.session.refresh(booking)

        return jsonify({"message": "Booking cancelled", "booking": booking.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        print("Cancel booking error:", str(e))
        return jsonify({"message": "Failed to cancel booking", "error": str(e)}), 500


# -----------------------------
# Get User Bookings
# -----------------------------
@booking_bp.route("/", methods=["GET"])
@login_required
def get_user_bookings():
    try:
        user_id = session.get("user_id")
        status = request.args.get("status")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        query = Booking.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)

        pagination = query.order_by(Booking.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        bookings = pagination.items

        return jsonify({
            "bookings": [b.to_dict() for b in bookings],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }), 200

    except Exception as e:
        print("Get bookings error:", str(e))
        return jsonify({"message": "Failed to fetch bookings", "error": str(e)}), 500
