from flask import Blueprint, request, jsonify, session
from datetime import datetime
from app.extensions import db
from app.models.booking import Booking
from app.models.adventure import Adventure
from app.models.payment import Payment
from app.utils.mpesa_utils import initiate_stk_push
from app.utils.helpers import login_required, validate_required_fields

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/', methods=['POST'])
@login_required
def create_booking():
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['adventure_id', 'adventure_date', 'number_of_people']
        is_valid, error_message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({'message': error_message}), 400
        
        adventure_id = data.get('adventure_id')
        adventure_date = data.get('adventure_date')
        number_of_people = data.get('number_of_people')
        special_requests = data.get('special_requests', '')
        
        # Validate adventure exists and is active
        adventure = Adventure.query.filter_by(id=adventure_id, is_active=True).first_or_404()
        
        # Validate adventure date is in the future
        try:
            adventure_datetime = datetime.fromisoformat(adventure_date.replace('Z', '+00:00'))
            if adventure_datetime < datetime.now():
                return jsonify({'message': 'Adventure date must be in the future'}), 400
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use ISO format'}), 400
        
        # Validate number of people
        if number_of_people < 1:
            return jsonify({'message': 'Number of people must be at least 1'}), 400
        
        # Check availability
        confirmed_bookings = Booking.query.filter(
            Booking.adventure_id == adventure_id,
            db.func.date(Booking.adventure_date) == adventure_datetime.date(),
            Booking.status == 'confirmed'
        ).count()
        
        available_slots = adventure.max_capacity - confirmed_bookings
        if number_of_people > available_slots:
            return jsonify({
                'message': f'Only {available_slots} slots available for this date',
                'available_slots': available_slots
            }), 400
        
        # Create booking
        booking = Booking(
            user_id=user_id,
            adventure_id=adventure_id,
            adventure_date=adventure_datetime,
            number_of_people=number_of_people,
            special_requests=special_requests
        )
        
        # Calculate total amount
        booking.calculate_total_amount()
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            'message': 'Booking created successfully',
            'booking': booking.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create booking', 'error': str(e)}), 500

@booking_bp.route('/initiate-payment', methods=['POST'])
@login_required
def initiate_booking_payment():
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        booking_id = data.get('booking_id')
        phone_number = data.get('phone_number')
        
        if not booking_id or not phone_number:
            return jsonify({'message': 'Booking ID and phone number are required'}), 400
        
        # Validate booking exists and belongs to user
        booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first_or_404()
        
        # Check if booking is already paid
        if booking.payment_id and booking.status == 'confirmed':
            return jsonify({'message': 'Booking is already paid and confirmed'}), 400
        
        # Check if booking is pending
        if booking.status != 'pending':
            return jsonify({'message': 'Cannot process payment for this booking status'}), 400
        
        # Initiate STK push for the booking amount
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
            adventure_id=booking.adventure_id
        )
        
        db.session.add(payment)
        db.session.flush()  # Get payment ID without committing
        
        # Link payment to booking
        booking.payment_id = payment.id
        
        db.session.commit()
        
        return jsonify({
            'message': 'Payment initiated successfully',
            'response': response,
            'booking_reference': booking.booking_reference,
            'payment_id': payment.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@booking_bp.route('/', methods=['GET'])
@login_required
def get_user_bookings():
    try:
        user_id = session.get('user_id')
        
        # Get query parameters for filtering
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Base query
        query = Booking.query.filter_by(user_id=user_id)
        
        # Filter by status if provided
        if status:
            query = query.filter_by(status=status)
        
        # Order by creation date (newest first)
        query = query.order_by(Booking.created_at.desc())
        
        # Pagination
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        bookings = pagination.items
        
        return jsonify({
            'bookings': [booking.to_dict() for booking in bookings],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch bookings', 'error': str(e)}), 500

@booking_bp.route('/<int:booking_id>', methods=['GET'])
@login_required
def get_booking(booking_id):
    try:
        user_id = session.get('user_id')
        booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first_or_404()
        
        return jsonify({
            'booking': booking.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch booking', 'error': str(e)}), 500

@booking_bp.route('/<int:booking_id>', methods=['PUT'])
@login_required
def update_booking(booking_id):
    try:
        user_id = session.get('user_id')
        booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first_or_404()
        
        # Only allow updates for pending bookings
        if booking.status != 'pending':
            return jsonify({'message': 'Can only update pending bookings'}), 400
        
        data = request.get_json()
        
        # Update allowed fields
        if 'adventure_date' in data:
            try:
                adventure_datetime = datetime.fromisoformat(data['adventure_date'].replace('Z', '+00:00'))
                if adventure_datetime < datetime.now():
                    return jsonify({'message': 'Adventure date must be in the future'}), 400
                booking.adventure_date = adventure_datetime
            except ValueError:
                return jsonify({'message': 'Invalid date format. Use ISO format'}), 400
        
        if 'number_of_people' in data:
            if data['number_of_people'] < 1:
                return jsonify({'message': 'Number of people must be at least 1'}), 400
            booking.number_of_people = data['number_of_people']
            booking.calculate_total_amount()  # Recalculate total amount
        
        if 'special_requests' in data:
            booking.special_requests = data['special_requests']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Booking updated successfully',
            'booking': booking.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update booking', 'error': str(e)}), 500

@booking_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    try:
        user_id = session.get('user_id')
        booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first_or_404()
        
        # Only allow cancellation for pending or confirmed bookings
        if booking.status not in ['pending', 'confirmed']:
            return jsonify({'message': 'Cannot cancel booking with current status'}), 400
        
        booking.status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'message': 'Booking cancelled successfully',
            'booking': booking.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to cancel booking', 'error': str(e)}), 500

@booking_bp.route('/adventure/<int:adventure_id>/availability', methods=['GET'])
def check_availability(adventure_id):
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'message': 'Date parameter is required'}), 400
    
    try:
        check_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use ISO format'}), 400
    
    # Count confirmed bookings for that date
    confirmed_bookings = Booking.query.filter(
        Booking.adventure_id == adventure_id,
        db.func.date(Booking.adventure_date) == check_date,
        Booking.status == 'confirmed'
    ).count()
    
    adventure = Adventure.query.get(adventure_id)
    max_capacity = adventure.max_capacity if adventure else 10
    available_slots = max_capacity - confirmed_bookings
    
    return jsonify({
        'date': check_date.isoformat(),
        'adventure_id': adventure_id,
        'confirmed_bookings': confirmed_bookings,
        'available_slots': available_slots,
        'is_available': available_slots > 0
    }), 200