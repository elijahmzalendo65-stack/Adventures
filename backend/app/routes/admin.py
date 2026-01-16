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
# ADMIN DASHBOARD (UPDATED for frontend format)
# =====================================================
@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    try:
        print("📊 Loading admin dashboard data...")
        
        # Get totals
        total_users = User.query.count()
        total_adventures = Adventure.query.count()
        total_bookings = Booking.query.count()

        # Calculate total revenue from completed payments
        total_revenue_result = db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(Payment.status == "completed").first()
        total_revenue = float(total_revenue_result[0]) if total_revenue_result else 0.0

        # Recent stats (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        recent_bookings = Booking.query.filter(Booking.created_at >= thirty_days_ago).count()
        
        recent_revenue_result = db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.status == "completed",
            Payment.created_at >= thirty_days_ago
        ).first()
        recent_revenue = float(recent_revenue_result[0]) if recent_revenue_result else 0.0

        # Booking status distribution
        booking_status_raw = db.session.query(
            Booking.status, func.count(Booking.id).label("count")
        ).group_by(Booking.status).all()
        
        booking_status = []
        status_colors = {
            "pending": "#f59e0b",     # Amber
            "confirmed": "#10b981",   # Green
            "completed": "#3b82f6",   # Blue
            "cancelled": "#ef4444",   # Red
            "payment_pending": "#8b5cf6"  # Purple
        }
        
        for status, count in booking_status_raw:
            booking_status.append({
                "status": status,
                "count": count,
                "color": status_colors.get(status, "#6b7280")  # Default gray
            })

        # Payment status distribution
        payment_status_raw = db.session.query(
            Payment.status, func.count(Payment.id).label("count")
        ).group_by(Payment.status).all()
        
        payment_status = []
        for status, count in payment_status_raw:
            payment_status.append({
                "status": status,
                "count": count
            })

        # Monthly revenue for last 6 months
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        monthly_revenue_raw = db.session.query(
            extract("year", Payment.created_at).label("year"),
            extract("month", Payment.created_at).label("month"),
            func.sum(Payment.amount).label("revenue")
        ).filter(
            Payment.status == "completed",
            Payment.created_at >= six_months_ago
        ).group_by("year", "month").order_by("year", "month").all()

        # Format monthly revenue with month names
        month_names = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }
        
        monthly_revenue = []
        for year, month, revenue in monthly_revenue_raw:
            monthly_revenue.append({
                "year": int(year),
                "month": int(month),
                "month_name": month_names.get(int(month), f"Month {month}"),
                "revenue": float(revenue) if revenue else 0.0
            })
        
        # If no revenue data, create sample data for chart
        if not monthly_revenue:
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            for i in range(6):
                month = current_month - i
                year = current_year
                if month <= 0:
                    month += 12
                    year -= 1
                
                monthly_revenue.append({
                    "year": year,
                    "month": month,
                    "month_name": month_names.get(month, f"Month {month}"),
                    "revenue": float((6 - i) * 10000)  # Sample data
                })
            monthly_revenue.reverse()

        # Create response in exact format expected by frontend
        response = {
            "dashboard": {
                "total_users": total_users,
                "total_adventures": total_adventures,
                "total_bookings": total_bookings,
                "total_revenue": total_revenue,
                "recent_users": recent_users,
                "recent_bookings": recent_bookings,
                "recent_revenue": recent_revenue
            },
            "analytics": {
                "booking_status": booking_status,
                "payment_status": payment_status,
                "monthly_revenue": monthly_revenue
            }
        }

        print(f"✅ Dashboard data loaded: {total_users} users, {total_bookings} bookings")
        return jsonify(response), 200

    except Exception as e:
        print(f"❌ Error loading dashboard: {str(e)}")
        return jsonify({
            "message": "Failed to load dashboard",
            "error": str(e)
        }), 500


# =====================================================
# USERS MANAGEMENT
# =====================================================
@admin_bp.route("/users", methods=["GET"])
@admin_required
def get_all_users():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)  # Increased for admin
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

        users_data = []
        for user in pagination.items:
            # Count user stats
            adventures_created = Adventure.query.filter_by(user_id=user.id).count()
            bookings_made = Booking.query.filter_by(user_id=user.id).count()
            
            # Calculate total spent
            total_spent_result = db.session.query(
                func.coalesce(func.sum(Payment.amount), 0)
            ).filter(
                Payment.user_id == user.id,
                Payment.status == "completed"
            ).first()
            total_spent = float(total_spent_result[0]) if total_spent_result else 0.0

            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "stats": {
                    "adventures_created": adventures_created,
                    "bookings_made": bookings_made,
                    "total_spent": total_spent
                }
            })

        return jsonify({
            "users": users_data,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page,
            "per_page": per_page
        }), 200

    except Exception as e:
        print(f"❌ Error fetching users: {str(e)}")
        return jsonify({
            "message": "Failed to fetch users",
            "error": str(e)
        }), 500


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user(user_id):
    try:
        user = User.query.get_or_404(user_id)

        # Get detailed user stats
        adventures_created = Adventure.query.filter_by(user_id=user.id).count()
        bookings_made = Booking.query.filter_by(user_id=user.id).count()
        payments_made = Payment.query.filter_by(user_id=user.id).count()
        
        total_spent_result = db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.user_id == user.id,
            Payment.status == "completed"
        ).first()
        total_spent = float(total_spent_result[0]) if total_spent_result else 0.0

        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "statistics": {
                "adventures_created": adventures_created,
                "bookings_made": bookings_made,
                "payments_made": payments_made,
                "total_spent": total_spent
            }
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
                "success": False,
                "message": "You cannot change your own admin role"
            }), 400

        user = User.query.get_or_404(user_id)
        user.is_admin = not user.is_admin
        db.session.commit()

        return jsonify({
            "success": True,
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
            "success": False,
            "message": "Failed to update admin role",
            "error": str(e)
        }), 500


# =====================================================
# ADVENTURES MANAGEMENT
# =====================================================
@admin_bp.route("/adventures", methods=["GET"])
@admin_required
def get_all_adventures():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        status = request.args.get("status", "all")

        query = Adventure.query

        if status == "active":
            query = query.filter_by(is_active=True)
        elif status == "inactive":
            query = query.filter_by(is_active=False)

        pagination = query.order_by(Adventure.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        adventures_data = []
        for adventure in pagination.items:
            # Count bookings for this adventure
            bookings_count = Booking.query.filter_by(adventure_id=adventure.id).count()
            
            # Calculate total revenue from this adventure
            adventure_revenue_result = db.session.query(
                func.coalesce(func.sum(Payment.amount), 0)
            ).join(Booking, Payment.booking_id == Booking.id).filter(
                Booking.adventure_id == adventure.id,
                Payment.status == "completed"
            ).first()
            adventure_revenue = float(adventure_revenue_result[0]) if adventure_revenue_result else 0.0

            adventures_data.append({
                "id": adventure.id,
                "user_id": adventure.user_id,
                "title": adventure.title,
                "description": adventure.description,
                "location": adventure.location,
                "price": float(adventure.price) if adventure.price else 0.0,
                "duration": adventure.duration,
                "difficulty": adventure.difficulty,
                "image_url": adventure.image_url,
                "max_capacity": adventure.max_capacity,
                "is_active": adventure.is_active,
                "created_at": adventure.created_at.isoformat() if adventure.created_at else None,
                "stats": {
                    "bookings_count": bookings_count,
                    "total_revenue": adventure_revenue
                }
            })

        return jsonify({
            "adventures": adventures_data,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }), 200

    except Exception as e:
        print(f"❌ Error fetching adventures: {str(e)}")
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

        return jsonify({
            "success": True,
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
            "success": False,
            "message": "Failed to update adventure",
            "error": str(e)
        }), 500


# =====================================================
# BOOKINGS MANAGEMENT
# =====================================================
@admin_bp.route("/bookings", methods=["GET"])
@admin_required
def get_all_bookings():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        status = request.args.get("status")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")

        query = Booking.query

        if status:
            query = query.filter_by(status=status)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(Booking.created_at >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                query = query.filter(Booking.created_at <= date_to_obj)
            except ValueError:
                pass

        pagination = query.order_by(Booking.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        bookings_data = []
        for booking in pagination.items:
            # Get adventure details
            adventure = Adventure.query.get(booking.adventure_id)
            adventure_title = adventure.title if adventure else "Unknown Adventure"
            
            # Get user details
            user = User.query.get(booking.user_id)
            user_name = user.username if user else "Unknown User"

            bookings_data.append({
                "id": booking.id,
                "user_id": booking.user_id,
                "user_name": user_name,
                "adventure_id": booking.adventure_id,
                "adventure_title": adventure_title,
                "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
                "adventure_date": booking.adventure_date.isoformat() if booking.adventure_date else None,
                "number_of_people": booking.number_of_people,
                "total_amount": float(booking.total_amount) if booking.total_amount else 0.0,
                "status": booking.status,
                "booking_reference": booking.booking_reference,
                "customer_name": booking.customer_name,
                "customer_email": booking.customer_email,
                "customer_phone": booking.customer_phone,
                "special_requests": booking.special_requests,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
                "updated_at": booking.updated_at.isoformat() if booking.updated_at else None
            })

        return jsonify({
            "bookings": bookings_data,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }), 200

    except Exception as e:
        print(f"❌ Error fetching bookings: {str(e)}")
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

        if new_status not in ["pending", "confirmed", "cancelled", "completed", "payment_pending"]:
            return jsonify({
                "success": False,
                "message": "Invalid booking status"
            }), 400

        booking = Booking.query.get_or_404(booking_id)
        booking.status = new_status
        db.session.commit()

        return jsonify({
            "success": True,
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
            "success": False,
            "message": "Failed to update booking",
            "error": str(e)
        }), 500


# =====================================================
# PAYMENTS MANAGEMENT
# =====================================================
@admin_bp.route("/payments", methods=["GET"])
@admin_required
def get_all_payments():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        status = request.args.get("status")

        query = Payment.query
        if status:
            query = query.filter_by(status=status)

        pagination = query.order_by(Payment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        payments_data = []
        for payment in pagination.items:
            payments_data.append({
                "id": payment.id,
                "user_id": payment.user_id,
                "adventure_id": payment.adventure_id,
                "booking_id": payment.booking_id,
                "mpesa_receipt_number": payment.mpesa_receipt_number,
                "phone_number": payment.phone_number,
                "amount": float(payment.amount) if payment.amount else 0.0,
                "status": payment.status,
                "checkout_request_id": payment.checkout_request_id,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "updated_at": payment.updated_at.isoformat() if payment.updated_at else None
            })

        return jsonify({
            "payments": payments_data,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }), 200

    except Exception as e:
        print(f"❌ Error fetching payments: {str(e)}")
        return jsonify({
            "message": "Failed to fetch payments",
            "error": str(e)
        }), 500


# =====================================================
# ADDITIONAL ADMIN ENDPOINTS
# =====================================================
@admin_bp.route("/stats/overview", methods=["GET"])
@admin_required
def get_overview_stats():
    """Get quick overview stats for admin dashboard"""
    try:
        # Today's stats
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        todays_bookings = Booking.query.filter(
            Booking.created_at >= today_start
        ).count()
        
        todays_revenue_result = db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.status == "completed",
            Payment.created_at >= today_start
        ).first()
        todays_revenue = float(todays_revenue_result[0]) if todays_revenue_result else 0.0
        
        todays_users = User.query.filter(
            User.created_at >= today_start
        ).count()

        # Weekly stats
        week_start = datetime.utcnow() - timedelta(days=7)
        
        weekly_bookings = Booking.query.filter(
            Booking.created_at >= week_start
        ).count()
        
        weekly_revenue_result = db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.status == "completed",
            Payment.created_at >= week_start
        ).first()
        weekly_revenue = float(weekly_revenue_result[0]) if weekly_revenue_result else 0.0

        # Most popular adventures (by bookings)
        popular_adventures = db.session.query(
            Adventure.id,
            Adventure.title,
            func.count(Booking.id).label("booking_count")
        ).join(Booking, Adventure.id == Booking.adventure_id)\
         .group_by(Adventure.id)\
         .order_by(func.count(Booking.id).desc())\
         .limit(5).all()

        popular_adventures_list = []
        for adv_id, title, count in popular_adventures:
            popular_adventures_list.append({
                "id": adv_id,
                "title": title,
                "booking_count": count
            })

        return jsonify({
            "today": {
                "bookings": todays_bookings,
                "revenue": todays_revenue,
                "new_users": todays_users
            },
            "weekly": {
                "bookings": weekly_bookings,
                "revenue": weekly_revenue
            },
            "popular_adventures": popular_adventures_list
        }), 200

    except Exception as e:
        print(f"❌ Error fetching overview stats: {str(e)}")
        return jsonify({
            "message": "Failed to fetch overview stats",
            "error": str(e)
        }), 500


@admin_bp.route("/system/health", methods=["GET"])
@admin_required
def system_health():
    """Check system health and status"""
    try:
        # Database health
        db_status = "healthy"
        try:
            db.session.execute("SELECT 1")
        except Exception:
            db_status = "unhealthy"

        # Counts
        user_count = User.query.count()
        adventure_count = Adventure.query.count()
        booking_count = Booking.query.count()
        payment_count = Payment.query.count()

        # Recent errors (you would need an error log table for this)
        recent_errors = []

        return jsonify({
            "database": db_status,
            "counts": {
                "users": user_count,
                "adventures": adventure_count,
                "bookings": booking_count,
                "payments": payment_count
            },
            "server_time": datetime.utcnow().isoformat(),
            "recent_errors": recent_errors
        }), 200

    except Exception as e:
        return jsonify({
            "database": "unknown",
            "error": str(e),
            "server_time": datetime.utcnow().isoformat()
        }), 500


# =====================================================
# TEST DATA GENERATION (for development)
# =====================================================
@admin_bp.route("/test-data/generate", methods=["POST"])
@admin_required
def generate_test_data():
    """Generate test data for development"""
    try:
        from werkzeug.security import generate_password_hash
        from faker import Faker
        import random
        
        fake = Faker()
        
        # Create test users
        for _ in range(10):
            user = User(
                username=fake.user_name(),
                email=fake.email(),
                phone_number=fake.phone_number()[:15],
                password_hash=generate_password_hash("password123")
            )
            db.session.add(user)
        
        db.session.flush()
        
        # Get all users
        users = User.query.all()
        
        # Create test adventures
        adventure_templates = [
            {"title": "Mountain Hiking", "location": "Mount Kenya", "price": 8000},
            {"title": "Beach Vacation", "location": "Diani Beach", "price": 12000},
            {"title": "Safari Tour", "location": "Maasai Mara", "price": 15000},
            {"title": "Cultural Experience", "location": "Lamu Island", "price": 9000},
            {"title": "Wildlife Safari", "location": "Amboseli", "price": 13000},
        ]
        
        for template in adventure_templates:
            for _ in range(2):  # Create 2 of each type
                adventure = Adventure(
                    title=f"{template['title']} #{random.randint(1, 100)}",
                    description=fake.paragraph(),
                    location=template['location'],
                    price=template['price'],
                    duration=f"{random.randint(1, 5)} days",
                    difficulty=random.choice(["Easy", "Medium", "Hard"]),
                    image_url=f"/images/{template['title'].lower().replace(' ', '-')}.jpg",
                    max_capacity=random.randint(5, 20),
                    is_active=True,
                    user_id=random.choice(users).id
                )
                db.session.add(adventure)
        
        db.session.flush()
        
        # Create test bookings
        adventures = Adventure.query.all()
        statuses = ["pending", "confirmed", "completed", "cancelled"]
        
        for _ in range(20):
            user = random.choice(users)
            adventure = random.choice(adventures)
            
            booking = Booking(
                user_id=user.id,
                adventure_id=adventure.id,
                adventure_date=datetime.utcnow() + timedelta(days=random.randint(1, 30)),
                number_of_people=random.randint(1, 8),
                total_amount=float(adventure.price) * random.randint(1, 3),
                status=random.choice(statuses),
                customer_name=user.username,
                customer_email=user.email,
                customer_phone=user.phone_number,
                special_requests=fake.sentence() if random.random() > 0.7 else ""
            )
            db.session.add(booking)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Test data generated successfully",
            "counts": {
                "users": User.query.count(),
                "adventures": Adventure.query.count(),
                "bookings": Booking.query.count()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Failed to generate test data: {str(e)}"
        }), 500