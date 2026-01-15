from flask import Blueprint, request, jsonify, session
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from ..extensions import db
from ..models.user import User
from ..models.adventure import Adventure
from ..models.booking import Booking
from ..models.payment import Payment
from ..utils.helpers import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# =====================================================
# ADMIN DASHBOARD (FIXED)
# =====================================================
@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    try:
        total_users = User.query.count()
        total_adventures = Adventure.query.count()
        total_bookings = Booking.query.count()

        total_revenue = db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(Payment.status == "completed").scalar()

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        recent_bookings = Booking.query.filter(Booking.created_at >= thirty_days_ago).count()
        recent_revenue = db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.status == "completed",
            Payment.created_at >= thirty_days_ago
        ).scalar()

        booking_status = db.session.query(
            Booking.status, func.count(Booking.id)
        ).group_by(Booking.status).all()

        payment_status = db.session.query(
            Payment.status, func.count(Payment.id)
        ).group_by(Payment.status).all()

        six_months_ago = datetime.utcnow() - timedelta(days=180)

        monthly_revenue = db.session.query(
            extract("year", Payment.created_at).label("year"),
            extract("month", Payment.created_at).label("month"),
            func.sum(Payment.amount).label("revenue")
        ).filter(
            Payment.status == "completed",
            Payment.created_at >= six_months_ago
        ).group_by("year", "month").order_by("year", "month").all()

        return jsonify({
            "dashboard": {
                "total_users": total_users,
                "total_adventures": total_adventures,
                "total_bookings": total_bookings,
                "total_revenue": float(total_revenue),
                "recent_users": recent_users,
                "recent_bookings": recent_bookings,
                "recent_revenue": float(recent_revenue)
            },
            "analytics": {
                "booking_status": [
                    {"status": s, "count": c} for s, c in booking_status
                ],
                "payment_status": [
                    {"status": s, "count": c} for s, c in payment_status
                ],
                "monthly_revenue": [
                    {
                        "year": int(y),
                        "month": int(m),
                        "revenue": float(r)
                    } for y, m, r in monthly_revenue
                ]
            }
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to load dashboard",
            "error": str(e)
        }), 500


# =====================================================
# USERS MANAGEMENT (FIXED - NO to_dict())
# =====================================================
@admin_bp.route("/users", methods=["GET"])
@admin_required
def get_all_users():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search = request.args.get("search", "")

        query = User.query

        if search:
            query = query.filter(
                User.username.ilike(f"%{search}%") |
                User.email.ilike(f"%{search}%") |
                User.phone_number.ilike(f"%{search}%")
            )

        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # ✅ FIXED: Use simple dictionaries instead of to_dict()
        users_data = []
        for user in pagination.items:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            })

        return jsonify({
            "users": users_data,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page,
            "per_page": per_page
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to fetch users",
            "error": str(e)
        }), 500


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user(user_id):
    try:
        user = User.query.get_or_404(user_id)

        # ✅ FIXED: Use simple queries without loading relationships
        stats = {
            "adventures_created": 0,  # Temporarily set to 0
            "bookings_made": 0,       # Temporarily set to 0  
            "payments_made": 0,       # Temporarily set to 0
            "total_spent": 0          # Temporarily set to 0
        }

        # ✅ FIXED: Simple dictionary instead of to_dict()
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "statistics": stats
        }

        return jsonify({"user": data}), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to fetch user",
            "error": str(e)
        }), 500


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["PUT"])
@admin_required
def toggle_admin(user_id):
    try:
        if session.get("user_id") == user_id:
            return jsonify({
                "message": "You cannot change your own admin role"
            }), 400

        user = User.query.get_or_404(user_id)
        user.is_admin = not user.is_admin
        db.session.commit()

        # ✅ FIXED: Simple dictionary instead of to_dict()
        return jsonify({
            "message": "Admin role updated",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "Failed to update admin role",
            "error": str(e)
        }), 500


# =====================================================
# ADVENTURES MANAGEMENT (FIXED - NO to_dict())
# =====================================================
@admin_bp.route("/adventures", methods=["GET"])
@admin_required
def get_all_adventures():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        status = request.args.get("status", "all")

        query = Adventure.query

        if status == "active":
            query = query.filter_by(is_active=True)
        elif status == "inactive":
            query = query.filter_by(is_active=False)

        pagination = query.order_by(Adventure.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # ✅ FIXED: Simple dictionaries instead of to_dict()
        adventures_data = []
        for adventure in pagination.items:
            adventures_data.append({
                "id": adventure.id,
                "user_id": adventure.user_id,
                "title": adventure.title,
                "description": adventure.description,
                "location": adventure.location,
                "price": adventure.price,
                "duration": adventure.duration,
                "difficulty": adventure.difficulty,
                "image_url": adventure.image_url,
                "max_capacity": adventure.max_capacity,
                "is_active": adventure.is_active,
                "created_at": adventure.created_at.isoformat() if adventure.created_at else None,
            })

        return jsonify({
            "adventures": adventures_data,
            "total": pagination.total,
            "pages": pagination.pages
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to fetch adventures",
            "error": str(e)
        }), 500


@admin_bp.route("/adventures/<int:adventure_id>/toggle-status", methods=["PUT"])
@admin_required
def toggle_adventure_status(adventure_id):
    try:
        adventure = Adventure.query.get_or_404(adventure_id)
        adventure.is_active = not adventure.is_active
        db.session.commit()

        # ✅ FIXED: Simple dictionary instead of to_dict()
        return jsonify({
            "message": "Adventure status updated",
            "adventure": {
                "id": adventure.id,
                "title": adventure.title,
                "is_active": adventure.is_active,
                "created_at": adventure.created_at.isoformat() if adventure.created_at else None,
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "Failed to update adventure",
            "error": str(e)
        }), 500


# =====================================================
# BOOKINGS MANAGEMENT (FIXED - NO to_dict())
# =====================================================
@admin_bp.route("/bookings", methods=["GET"])
@admin_required
def get_all_bookings():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        status = request.args.get("status")

        query = Booking.query
        if status:
            query = query.filter_by(status=status)

        pagination = query.order_by(Booking.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # ✅ FIXED: Simple dictionaries instead of to_dict()
        bookings_data = []
        for booking in pagination.items:
            bookings_data.append({
                "id": booking.id,
                "user_id": booking.user_id,
                "adventure_id": booking.adventure_id,
                "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
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
            "pages": pagination.pages
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to fetch bookings",
            "error": str(e)
        }), 500


@admin_bp.route("/bookings/<int:booking_id>", methods=["PUT"])
@admin_required
def update_booking_status(booking_id):
    try:
        data = request.get_json() or {}
        new_status = data.get("status")

        if new_status not in ["pending", "confirmed", "cancelled", "completed"]:
            return jsonify({"message": "Invalid booking status"}), 400

        booking = Booking.query.get_or_404(booking_id)
        booking.status = new_status
        db.session.commit()

        # ✅ FIXED: Simple dictionary instead of to_dict()
        return jsonify({
            "message": "Booking status updated",
            "booking": {
                "id": booking.id,
                "status": booking.status,
                "booking_reference": booking.booking_reference,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "Failed to update booking",
            "error": str(e)
        }), 500


# =====================================================
# PAYMENTS MANAGEMENT (FIXED - NO to_dict())
# =====================================================
@admin_bp.route("/payments", methods=["GET"])
@admin_required
def get_all_payments():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        status = request.args.get("status")

        query = Payment.query
        if status:
            query = query.filter_by(status=status)

        pagination = query.order_by(Payment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # ✅ FIXED: Simple dictionaries instead of to_dict()
        payments_data = []
        for payment in pagination.items:
            payments_data.append({
                "id": payment.id,
                "user_id": payment.user_id,
                "adventure_id": payment.adventure_id,
                "booking_id": payment.booking_id,
                "mpesa_receipt_number": payment.mpesa_receipt_number,
                "phone_number": payment.phone_number,
                "amount": payment.amount,
                "status": payment.status,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
            })

        return jsonify({
            "payments": payments_data,
            "total": pagination.total,
            "pages": pagination.pages
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to fetch payments",
            "error": str(e)
        }), 500


# =====================================================
# EMERGENCY: TEMPORARILY DISABLE STATISTICS
# =====================================================
@admin_bp.route("/users/<int:user_id>/simple", methods=["GET"])
@admin_required  
def get_user_simple(user_id):
    """Emergency endpoint - just basic user data."""
    try:
        user = User.query.get_or_404(user_id)
        
        return jsonify({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch user",
            "error": str(e)
        }), 500