# app/routes/booking.py - UPDATED FOR SESSION-BASED AUTH
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone
from ..extensions import db
from ..models.booking import Booking
from ..models.adventure import Adventure
from ..models.payment import Payment
from ..models.user import User  # Import User model
import logging

logger = logging.getLogger(__name__)
booking_bp = Blueprint("booking", __name__)

# -----------------------------
# Helper function for session authentication
# -----------------------------
def get_current_user():
    """Get current user from session"""
    user_id = session.get("user_id")
    if not user_id:
        return None
    
    user = User.query.get(user_id)
    return user

def require_auth():
    """Check if user is authenticated via session"""
    user = get_current_user()
    if not user:
        return jsonify({
            "success": False,
            "message": "Authentication required",
            "error": "Please login to access this resource"
        }), 401
    return user

# -----------------------------
# TEST ENDPOINT (to verify API is working)
# -----------------------------
@booking_bp.route("/test", methods=["GET"])
def test_endpoint():
    """Test endpoint to verify booking API is working"""
    return jsonify({
        "success": True,
        "message": "Booking API is working!",
        "endpoints": {
            "POST /api/bookings/": "Create a new booking",
            "GET /api/bookings/": "Get user bookings",
            "GET /api/bookings/my-bookings": "Get current user bookings",
            "POST /api/bookings/initiate-payment": "Initiate payment for booking",
            "POST /api/bookings/<id>/cancel": "Cancel a booking"
        }
    }), 200

# -----------------------------
# CREATE BOOKING (UPDATED FOR SESSION AUTH)
# -----------------------------
@booking_bp.route("/", methods=["POST"])
def create_booking():
    """Create a new booking"""
    try:
        # Get user from session
        auth_result = require_auth()
        if isinstance(auth_result, tuple):  # It's an error response
            return auth_result
        user = auth_result
        
        user_id = user.id
        logger.info(f"Creating booking for user_id: {user_id}, username: {user.username}")
        
        data = request.get_json() or {}
        logger.info(f"Booking request data: {data}")
        
        # Extract data with fallbacks
        adventure_id = data.get("adventure_id")
        booking_date_str = data.get("booking_date") or data.get("adventure_date")
        participants = data.get("participants") or data.get("number_of_people", 1)
        
        # Get customer info (use logged-in user's info as defaults)
        customer_name = data.get("customer_name", user.username or user.name or "Guest")
        customer_email = data.get("customer_email", user.email or "")
        customer_phone = data.get("customer_phone", user.phone_number or "")
        special_requests = data.get("special_requests", "")
        
        # Validate required fields
        if not adventure_id:
            return jsonify({
                "success": False,
                "message": "Adventure ID is required"
            }), 400
            
        if not booking_date_str:
            return jsonify({
                "success": False,
                "message": "Booking date is required"
            }), 400
        
        # Validate adventure exists
        adventure = Adventure.query.filter_by(id=adventure_id, is_active=True).first()
        if not adventure:
            return jsonify({
                "success": False,
                "message": "Adventure not found or inactive"
            }), 404
        
        # Parse and validate date
        try:
            # Try ISO format first
            if 'T' in booking_date_str:
                booking_date = datetime.fromisoformat(booking_date_str.replace('Z', '+00:00'))
            else:
                # Try YYYY-MM-DD format
                booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d")
            
            # Ensure timezone aware
            if booking_date.tzinfo is None:
                booking_date = booking_date.replace(tzinfo=timezone.utc)
            else:
                booking_date = booking_date.astimezone(timezone.utc)
            
            # Check if date is in the future
            now = datetime.now(timezone.utc)
            if booking_date < now:
                return jsonify({
                    "success": False,
                    "message": "Booking date must be in the future"
                }), 400
                
        except ValueError as e:
            logger.error(f"Date parsing error: {e}")
            return jsonify({
                "success": False,
                "message": f"Invalid date format. Use YYYY-MM-DD or ISO format. Error: {str(e)}"
            }), 400
        
        # Validate participants
        try:
            participants = int(participants)
            if participants < 1:
                return jsonify({
                    "success": False,
                    "message": "Number of participants must be at least 1"
                }), 400
                
            # Check against adventure's max capacity if available
            if hasattr(adventure, 'max_capacity') and adventure.max_capacity:
                if participants > adventure.max_capacity:
                    return jsonify({
                        "success": False,
                        "message": f"Maximum {adventure.max_capacity} participants allowed for this adventure"
                    }), 400
            elif participants > 20:  # Default limit
                return jsonify({
                    "success": False,
                    "message": "Maximum 20 participants per booking"
                }), 400
                
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Invalid number of participants"
            }), 400
        
        # Calculate total amount
        total_amount = float(adventure.price) * participants
        
        # Create booking
        booking = Booking(
            user_id=user_id,
            adventure_id=adventure.id,
            adventure_date=booking_date,
            number_of_people=participants,
            total_amount=total_amount,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            special_requests=special_requests,
            status="pending"
        )
        
        db.session.add(booking)
        db.session.commit()
        
        logger.info(f"✅ Booking created successfully: {booking.booking_reference}")
        
        return jsonify({
            "success": True,
            "message": "Booking created successfully",
            "booking": {
                "id": booking.id,
                "booking_reference": booking.booking_reference,
                "adventure_id": booking.adventure_id,
                "adventure_title": adventure.title,
                "adventure_date": booking.adventure_date.isoformat(),
                "participants": booking.number_of_people,
                "total_amount": booking.total_amount,
                "status": booking.status,
                "customer_name": booking.customer_name,
                "customer_email": booking.customer_email,
                "created_at": booking.created_at.isoformat(),
                "special_requests": booking.special_requests
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Booking creation failed: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to create booking: {str(e)}"
        }), 500

# -----------------------------
# GET USER BOOKINGS (UPDATED FOR SESSION AUTH)
# -----------------------------
@booking_bp.route("/", methods=["GET"])
def get_user_bookings():
    """Get all bookings for the current user"""
    try:
        # Get user from session
        auth_result = require_auth()
        if isinstance(auth_result, tuple):  # It's an error response
            return auth_result
        user = auth_result
        
        user_id = user.id
        
        # Get optional query parameters
        status = request.args.get("status")
        limit = request.args.get("limit", 50, type=int)
        
        # Build base query
        query = db.session.query(Booking, Adventure).join(
            Adventure, Booking.adventure_id == Adventure.id
        ).filter(
            Booking.user_id == user_id
        )
        
        # Apply status filter if provided
        if status:
            query = query.filter(Booking.status == status)
        
        # Execute query with ordering
        results = query.order_by(
            Booking.created_at.desc()
        ).limit(limit).all()
        
        # Format response
        bookings = []
        for booking, adventure in results:
            bookings.append({
                "id": booking.id,
                "booking_reference": booking.booking_reference,
                "adventure_id": booking.adventure_id,
                "adventure_title": adventure.title,
                "adventure_image": adventure.image_url,
                "adventure_date": booking.adventure_date.isoformat() if booking.adventure_date else None,
                "participants": booking.number_of_people,
                "total_amount": booking.total_amount,
                "status": booking.status,
                "customer_name": booking.customer_name,
                "customer_email": booking.customer_email,
                "special_requests": booking.special_requests,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
                "updated_at": booking.updated_at.isoformat() if booking.updated_at else None
            })
        
        return jsonify({
            "success": True,
            "bookings": bookings,
            "count": len(bookings),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching bookings: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to fetch bookings: {str(e)}"
        }), 500

# -----------------------------
# GET MY BOOKINGS (Alias for frontend compatibility)
# -----------------------------
@booking_bp.route("/my-bookings", methods=["GET"])
def get_my_bookings():
    """Alias for /api/bookings/ to match frontend expectations"""
    return get_user_bookings()

# -----------------------------
# INITIATE PAYMENT (UPDATED FOR SESSION AUTH)
# -----------------------------
@booking_bp.route("/initiate-payment", methods=["POST"])
def initiate_payment():
    """Initiate payment for a booking"""
    try:
        # Get user from session
        auth_result = require_auth()
        if isinstance(auth_result, tuple):  # It's an error response
            return auth_result
        user = auth_result
        
        user_id = user.id
        data = request.get_json() or {}
        
        booking_id = data.get("booking_id")
        phone_number = data.get("phone_number")
        
        if not booking_id or not phone_number:
            return jsonify({
                "success": False,
                "message": "Booking ID and phone number are required"
            }), 400
        
        # Get booking
        booking = Booking.query.filter_by(
            id=booking_id, 
            user_id=user_id
        ).first()
        
        if not booking:
            return jsonify({
                "success": False,
                "message": "Booking not found"
            }), 404
        
        if booking.status != "pending":
            return jsonify({
                "success": False,
                "message": f"Booking is already {booking.status}"
            }), 400
        
        # For now, create a mock payment record
        # In production, integrate with M-Pesa STK Push here
        payment = Payment(
            user_id=user_id,
            adventure_id=booking.adventure_id,
            booking_id=booking.id,
            phone_number=phone_number,
            amount=booking.total_amount,
            checkout_request_id=f"MOCK_{booking.id}_{datetime.now().timestamp()}",
            status="pending"
        )
        
        db.session.add(payment)
        
        # Update booking status
        booking.status = "payment_pending"
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Payment initiated successfully",
            "payment": {
                "id": payment.id,
                "booking_id": booking.id,
                "amount": payment.amount,
                "status": payment.status,
                "checkout_request_id": payment.checkout_request_id
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Payment initiation failed: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to initiate payment: {str(e)}"
        }), 500

# -----------------------------
# CANCEL BOOKING (UPDATED FOR SESSION AUTH)
# -----------------------------
@booking_bp.route("/<int:booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    """Cancel a booking"""
    try:
        # Get user from session
        auth_result = require_auth()
        if isinstance(auth_result, tuple):  # It's an error response
            return auth_result
        user = auth_result
        
        user_id = user.id
        
        # Get booking
        booking = Booking.query.filter_by(
            id=booking_id, 
            user_id=user_id
        ).first()
        
        if not booking:
            return jsonify({
                "success": False,
                "message": "Booking not found"
            }), 404
        
        # Check if booking can be cancelled
        if booking.status not in ["pending", "confirmed"]:
            return jsonify({
                "success": False,
                "message": f"Cannot cancel booking with status: {booking.status}"
            }), 400
        
        # Cancel the booking
        booking.status = "cancelled"
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Booking cancelled successfully",
            "booking": {
                "id": booking.id,
                "booking_reference": booking.booking_reference,
                "status": booking.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Booking cancellation failed: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to cancel booking: {str(e)}"
        }), 500

# -----------------------------
# GET BOOKING BY ID (UPDATED FOR SESSION AUTH)
# -----------------------------
@booking_bp.route("/<int:booking_id>", methods=["GET"])
def get_booking_by_id(booking_id):
    """Get a specific booking by ID"""
    try:
        # Get user from session
        auth_result = require_auth()
        if isinstance(auth_result, tuple):  # It's an error response
            return auth_result
        user = auth_result
        
        user_id = user.id
        
        # Get booking with adventure details
        booking = db.session.query(Booking, Adventure).join(
            Adventure, Booking.adventure_id == Adventure.id
        ).filter(
            Booking.id == booking_id,
            Booking.user_id == user_id
        ).first()
        
        if not booking:
            return jsonify({
                "success": False,
                "message": "Booking not found"
            }), 404
        
        booking_obj, adventure = booking
        
        return jsonify({
            "success": True,
            "booking": {
                "id": booking_obj.id,
                "booking_reference": booking_obj.booking_reference,
                "adventure_id": booking_obj.adventure_id,
                "adventure_title": adventure.title,
                "adventure_image": adventure.image_url,
                "adventure_date": booking_obj.adventure_date.isoformat() if booking_obj.adventure_date else None,
                "participants": booking_obj.number_of_people,
                "total_amount": booking_obj.total_amount,
                "status": booking_obj.status,
                "customer_name": booking_obj.customer_name,
                "customer_email": booking_obj.customer_email,
                "customer_phone": booking_obj.customer_phone,
                "special_requests": booking_obj.special_requests,
                "created_at": booking_obj.created_at.isoformat() if booking_obj.created_at else None,
                "updated_at": booking_obj.updated_at.isoformat() if booking_obj.updated_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching booking {booking_id}: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to fetch booking: {str(e)}"
        }), 500

# -----------------------------
# GET ALL BOOKINGS (Admin only - session-based auth)
# -----------------------------
@booking_bp.route("/all", methods=["GET"])
def get_all_bookings():
    """Get all bookings (admin only)"""
    try:
        # Get user from session
        auth_result = require_auth()
        if isinstance(auth_result, tuple):
            return auth_result
        user = auth_result
        
        # Check if user is admin
        if not user.is_admin:
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403
        
        # Get optional query parameters
        status = request.args.get("status")
        limit = request.args.get("limit", 100, type=int)
        
        # Build query
        query = db.session.query(Booking, Adventure, User).join(
            Adventure, Booking.adventure_id == Adventure.id
        ).join(
            User, Booking.user_id == User.id
        )
        
        # Apply status filter if provided
        if status:
            query = query.filter(Booking.status == status)
        
        # Execute query
        results = query.order_by(
            Booking.created_at.desc()
        ).limit(limit).all()
        
        # Format response
        bookings = []
        for booking, adventure, booking_user in results:
            bookings.append({
                "id": booking.id,
                "booking_reference": booking.booking_reference,
                "adventure_id": booking.adventure_id,
                "adventure_title": adventure.title,
                "user_id": booking.user_id,
                "user_name": booking_user.username,
                "user_email": booking_user.email,
                "adventure_date": booking.adventure_date.isoformat() if booking.adventure_date else None,
                "participants": booking.number_of_people,
                "total_amount": booking.total_amount,
                "status": booking.status,
                "customer_name": booking.customer_name,
                "customer_email": booking.customer_email,
                "created_at": booking.created_at.isoformat() if booking.created_at else None
            })
        
        return jsonify({
            "success": True,
            "bookings": bookings,
            "count": len(bookings)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching all bookings: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to fetch bookings: {str(e)}"
        }), 500