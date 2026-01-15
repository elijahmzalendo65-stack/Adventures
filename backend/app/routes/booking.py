# app/routes/booking.py - FIXED VERSION
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone
from ..extensions import db
from ..models.booking import Booking
from ..models.adventure import Adventure
from ..models.payment import Payment
from ..utils.helpers import login_required
# from ..utils.mpesa_utils import initiate_stk_push  # Optional for real payments

booking_bp = Blueprint("booking", __name__, url_prefix="/api/bookings")


# -----------------------------
# Create Booking (FIXED)
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

        # Validate and parse date
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

        # Check availability
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

        # ✅ FIXED: Return simple dictionary instead of to_dict()
        return jsonify({
            "message": "Booking created successfully",
            "booking": {
                "id": booking.id,
                "user_id": booking.user_id,
                "adventure_id": booking.adventure_id,
                "adventure_date": booking.adventure_date.isoformat() if booking.adventure_date else None,
                "number_of_people": booking.number_of_people,
                "total_amount": booking.total_amount,
                "status": booking.status,
                "booking_reference": booking.booking_reference,
                "customer_name": booking.customer_name,
                "customer_email": booking.customer_email,
                "customer_phone": booking.customer_phone,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print("Booking creation error:", str(e))
        return jsonify({"message": "Failed to create booking"}), 500


# -----------------------------
# Initiate Payment (FIXED - removed payment_id assignment)
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

        # Mock payment response
        response = {"CheckoutRequestID": f"MOCK_{booking.id}"}

        # Save payment record (NO payment_id assignment)
        payment = Payment(
            user_id=user_id,
            adventure_id=booking.adventure_id,
            booking_id=booking.id,  # ✅ CORRECT: Payment references booking, not vice versa
            phone_number=phone_number,
            amount=booking.total_amount,
            checkout_request_id=response["CheckoutRequestID"],
            status="pending"
        )
        db.session.add(payment)
        db.session.commit()

        return jsonify({
            "message": "Payment initiated successfully",
            "booking_id": booking.id,
            "payment_id": payment.id,
            "checkout_request_id": response["CheckoutRequestID"]
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Payment initiation error:", str(e))
        return jsonify({"message": "Failed to initiate payment"}), 500


# -----------------------------
# Cancel Booking (FIXED)
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

        # ✅ FIXED: Return simple dictionary
        return jsonify({
            "message": "Booking cancelled",
            "booking": {
                "id": booking.id,
                "status": booking.status,
                "booking_reference": booking.booking_reference,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Cancel booking error:", str(e))
        return jsonify({"message": "Failed to cancel booking"}), 500


# -----------------------------
# Get User Bookings (FIXED)
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

        # ✅ FIXED: Build simple dictionaries instead of to_dict()
        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                "id": booking.id,
                "user_id": booking.user_id,
                "adventure_id": booking.adventure_id,
                "adventure_date": booking.adventure_date.isoformat() if booking.adventure_date else None,
                "number_of_people": booking.number_of_people,
                "total_amount": booking.total_amount,
                "status": booking.status,
                "booking_reference": booking.booking_reference,
                "customer_name": booking.customer_name,
                "customer_email": booking.customer_email,
                "customer_phone": booking.customer_phone,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
            })

        return jsonify({
            "bookings": bookings_data,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }), 200

    except Exception as e:
        print("Get bookings error:", str(e))
        return jsonify({"message": "Failed to fetch bookings"}), 500


# -----------------------------
# EMERGENCY: Simple booking endpoint
# -----------------------------
@booking_bp.route("/simple", methods=["GET"])
@login_required
def get_simple_bookings():
    """Emergency endpoint - basic booking data only."""
    try:
        user_id = session.get("user_id")
        
        # Simple query without relationships
        bookings = db.session.execute(
            "SELECT id, booking_reference, status, created_at FROM bookings WHERE user_id = :user_id ORDER BY created_at DESC",
            {"user_id": user_id}
        ).fetchall()
        
        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                "id": booking.id,
                "booking_reference": booking.booking_reference,
                "status": booking.status,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
            })
        
        return jsonify({
            "bookings": bookings_data,
            "count": len(bookings_data)
        }), 200
        
    except Exception as e:
        return jsonify({"message": "Failed to fetch bookings"}), 500