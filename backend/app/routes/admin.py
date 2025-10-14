from flask import Blueprint, request, jsonify, session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from ..extensions import db
from ..models.user import User
from ..models.adventure import Adventure
from ..models.booking import Booking
from ..models.payment import Payment
from ..utils.helpers import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    try:
        
        total_users = User.query.count()
        total_adventures = Adventure.query.count()
        total_bookings = Booking.query.count()
        total_revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            Payment.status == 'completed'
        ).scalar()

        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        recent_bookings = Booking.query.filter(Booking.created_at >= thirty_days_ago).count()
        recent_revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            Payment.status == 'completed', Payment.created_at >= thirty_days_ago
        ).scalar()

        
        booking_status = db.session.query(Booking.status, func.count(Booking.id)).group_by(Booking.status).all()
        payment_status = db.session.query(Payment.status, func.count(Payment.id)).group_by(Payment.status).all()

        
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_revenue = db.session.query(
            extract('year', Payment.created_at).label('year'),
            extract('month', Payment.created_at).label('month'),
            func.sum(Payment.amount).label('revenue')
        ).filter(Payment.status == 'completed', Payment.created_at >= six_months_ago
        ).group_by('year', 'month').order_by('year', 'month').all()

        return jsonify({
            'dashboard': {
                'total_users': total_users,
                'total_adventures': total_adventures,
                'total_bookings': total_bookings,
                'total_revenue': float(total_revenue),
                'recent_users': recent_users,
                'recent_bookings': recent_bookings,
                'recent_revenue': float(recent_revenue)
            },
            'analytics': {
                'booking_status': [{'status': status, 'count': count} for status, count in booking_status],
                'payment_status': [{'status': status, 'count': count} for status, count in payment_status],
                'monthly_revenue': [
                    {'year': int(year), 'month': int(month), 'revenue': float(revenue)}
                    for year, month, revenue in monthly_revenue
                ]
            }
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch dashboard data', 'error': str(e)}), 500



@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')

        query = User.query
        if search:
            query = query.filter(
                (User.username.ilike(f'%{search}%')) |
                (User.email.ilike(f'%{search}%')) |
                (User.phone_number.ilike(f'%{search}%'))
            )

        pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items

        return jsonify({
            'users': [user.to_dict() for user in users],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch users', 'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    try:
        user = User.query.get_or_404(user_id)

        
        user_stats = {
            'adventures_created': Adventure.query.filter_by(user_id=user_id).count(),
            'bookings_made': Booking.query.filter_by(user_id=user_id).count(),
            'payments_made': Payment.query.filter_by(user_id=user_id).count(),
            'total_spent': float(
                db.session.query(func.coalesce(func.sum(Payment.amount), 0))
                .filter(Payment.user_id == user_id, Payment.status == 'completed')
                .scalar()
            )
        }

        user_data = user.to_dict()
        user_data['statistics'] = user_stats

        return jsonify({'user': user_data}), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch user', 'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['PUT'])
@admin_required
def toggle_admin(user_id):
    try:
        current_user_id = session.get('user_id')
        if current_user_id == user_id:
            return jsonify({'message': 'Cannot modify your own admin status'}), 400

        user = User.query.get_or_404(user_id)
        user.is_admin = not user.is_admin
        db.session.commit()

        action = "granted" if user.is_admin else "revoked"
        return jsonify({'message': f'Admin privileges {action}', 'user': user.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update admin status', 'error': str(e)}), 500



@admin_bp.route('/adventures', methods=['GET'])
@admin_required
def get_all_adventures():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', 'all')

        query = Adventure.query
        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)

        pagination = query.order_by(Adventure.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        adventures = pagination.items

        return jsonify({
            'adventures': [adventure.to_dict() for adventure in adventures],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch adventures', 'error': str(e)}), 500


@admin_bp.route('/adventures/<int:adventure_id>/toggle-status', methods=['PUT'])
@admin_required
def toggle_adventure_status(adventure_id):
    try:
        adventure = Adventure.query.get_or_404(adventure_id)
        adventure.is_active = not adventure.is_active
        db.session.commit()
        status = "activated" if adventure.is_active else "deactivated"
        return jsonify({'message': f'Adventure {status}', 'adventure': adventure.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update adventure status', 'error': str(e)}), 500


@admin_bp.route('/bookings', methods=['GET'])
@admin_required
def get_all_bookings():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '')

        query = Booking.query
        if status:
            query = query.filter_by(status=status)

        pagination = query.order_by(Booking.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
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


@admin_bp.route('/bookings/<int:booking_id>', methods=['PUT'])
@admin_required
def update_booking_status(booking_id):
    try:
        booking = Booking.query.get_or_404(booking_id)
        data = request.get_json()
        new_status = data.get('status')
        valid_statuses = ['pending', 'confirmed', 'cancelled', 'completed']

        if new_status not in valid_statuses:
            return jsonify({'message': 'Invalid status'}), 400

        booking.status = new_status
        db.session.commit()

        return jsonify({'message': 'Booking status updated', 'booking': booking.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update booking status', 'error': str(e)}), 500


@admin_bp.route('/payments', methods=['GET'])
@admin_required
def get_all_payments():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '')

        query = Payment.query
        if status:
            query = query.filter_by(status=status)

        pagination = query.order_by(Payment.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        payments = pagination.items

        return jsonify({
            'payments': [payment.to_dict() for payment in payments],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch payments', 'error': str(e)}), 500
