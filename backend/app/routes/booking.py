from flask import Blueprint, request, jsonify, session
from datetime import datetime
from ..extensions import db
from ..models.booking import Booking
from ..models.adventure import Adventure
from ..models.payment import Payment
from ..models.user import User
from ..utils.mpesa_utils import initiate_stk_push
from ..utils.helpers import login_required, validate_required_fields

booking_bp = Blueprint('booking', __name__, url_prefix='/api/bookings')


# -----------------------------
# Create a new booking
# -----------------------------
@booking_bp.route('/', methods=['POST'])
@login_required
def create_booking():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'message': 'Unauthorized'}), 401

        data = request.get_json() or {}

        # Validate required fields
        required_fields = ['adventure_id', 'adventure_date', 'number_of_people']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({'message': error_msg}), 400

        # Fetch adventure
        adventure = Adventure.query.filter_by(id=data['adventure_id'], is_active=True).first()
        if not adventure:
            return jsonify({'message': 'Adventure not found or inactive'}), 404

        # Parse adventure date
        try:
            adventure_date = datetime.fromisoformat(data['adventure_date'].replace('Z', '+00:00'))
            if adventure_date < datetime.utcnow():
                return jsonify({'message': 'Adventure date must be in the future'}), 400
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use ISO format'}), 400

        # Validate number_of_people
        number_of_people = int(data.get('number_of_people', 1))
        if number_of_people < 1:
            return jsonify({'message': 'Number of people must be at least 1'}), 400

        # Check availability
        confirmed_count = Booking.query.filter(
            Booking.adventure_id == adventure.id,
            db.func.date(Booking.adventure_date) == adventure_date.date(),
            Booking.status == 'confirmed'
        ).count()
        available_slots = adventure.max_capacity - confirmed_count
        if number_of_people > available_slots:
            return jsonify({
                'message': f'Only {available_slots} slots available',
                'available_slots': available_slots
            }), 400

        # Calculate total amount
        total_amount = adventure.price * number_of_people

        # Create booking
        booking = Booking(
            user_id=user_id,
            adventure_id=adventure.id,
            adventure_date=adventure_date,
            number_of_people=number_of_people,
            total_amount=total_amount,
            special_requests=data.get('special_requests', ''),
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        db.session.refresh(booking)

        return jsonify({'message': 'Booking created successfully', 'booking': booking.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create booking', 'error': str(e)}), 500


# -----------------------------
# Initiate M-Pesa payment
# -----------------------------
@booking_bp.route('/initiate-payment', methods=['POST'])
@login_required
def initiate_payment():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}

        booking_id = data.get('booking_id')
        phone_number = data.get('phone_number')

        if not booking_id or not phone_number:
            return jsonify({'message': 'Booking ID and phone number are required'}), 400

        if len(phone_number) < 10:
            return jsonify({'message': 'Enter a valid phone number'}), 400

        booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first()
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404

        if booking.status != 'pending':
            return jsonify({'message': 'Booking already paid or cancelled'}), 400

        # Initiate M-Pesa STK Push
        response = initiate_stk_push(
            phone_number=phone_number,
            amount=booking.total_amount,
            account_reference=f"BOOKING_{booking.booking_reference}",
            transaction_desc=f"Payment for booking {booking.booking_reference}"
        )

        # Create payment record
        payment = Payment(
            phone_number=phone_number,
            amount=booking.total_amount,
            checkout_request_id=response.get('CheckoutRequestID'),
            merchant_request_id=response.get('MerchantRequestID'),
            user_id=user_id,
            adventure_id=booking.adventure_id,
            status='pending'
        )
        db.session.add(payment)
        db.session.flush()  # Flush to get payment.id
        booking.payment_id = payment.id
        db.session.commit()
        db.session.refresh(booking)

        return jsonify({
            'message': 'Payment initiated successfully',
            'booking_reference': booking.booking_reference,
            'payment_id': payment.id,
            'response': response
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to initiate payment', 'error': str(e)}), 500


# -----------------------------
# Cancel booking
# -----------------------------
@booking_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    try:
        user_id = session.get('user_id')
        booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first()
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404

        if booking.status not in ['pending', 'confirmed']:
            return jsonify({'message': 'Cannot cancel this booking'}), 400

        booking.status = 'cancelled'
        db.session.commit()
        db.session.refresh(booking)

        return jsonify({'message': 'Booking cancelled', 'booking': booking.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to cancel booking', 'error': str(e)}), 500


# -----------------------------
# Fetch user bookings
# -----------------------------
@booking_bp.route('/', methods=['GET'])
@login_required
def get_user_bookings():
    try:
        user_id = session.get('user_id')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        query = Booking.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)

        pagination = query.order_by(Booking.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        bookings = pagination.items
        bookings_list = [b.to_dict() for b in bookings]

        return jsonify({
            'bookings': bookings_list,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch bookings', 'error': str(e)}), 500
