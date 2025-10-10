from flask import Blueprint, request, jsonify
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app.extensions import db
from app.models.user import User
from app.models.adventure import Adventure
from app.models.payment import Payment
from app.models.booking import Booking
from app.utils.helpers import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    try:
        # Total counts
        total_users = User.query.count()
        total_adventures = Adventure.query.count()
        total_bookings = Booking.query.count()
        total_revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            Payment.status == 'completed'
        ).scalar()

        # Recent activities (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        recent_users = User.query.filter(
            User.created_at >= thirty_days_ago
        ).count()
        
        recent_bookings = Booking.query.filter(
            Booking.created_at >= thirty_days_ago
        ).count()
        
        recent_revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            Payment.status == 'completed',
            Payment.created_at >= thirty_days_ago
        ).scalar()

        # Booking status distribution
        booking_status = db.session.query(
            Booking.status,
            func.count(Booking.id)
        ).group_by(Booking.status).all()

        # Payment status distribution
        payment_status = db.session.query(
            Payment.status,
            func.count(Payment.id)
        ).group_by(Payment.status).all()

        # Monthly revenue (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        
        monthly_revenue = db.session.query(
            extract('year', Payment.created_at).label('year'),
            extract('month', Payment.created_at).label('month'),
            func.sum(Payment.amount).label('revenue')
        ).filter(
            Payment.status == 'completed',
            Payment.created_at >= six_months_ago
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
                    {
                        'year': int(year),
                        'month': int(month),
                        'revenue': float(revenue)
                    } for year, month, revenue in monthly_revenue
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
        
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
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
        
        # Get user statistics
        user_adventures = Adventure.query.filter_by(user_id=user_id).count()
        user_bookings = Booking.query.filter_by(user_id=user_id).count()
        user_payments = Payment.query.filter_by(user_id=user_id).count()
        total_spent = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            Payment.user_id == user_id,
            Payment.status == 'completed'
        ).scalar()
        
        user_data = user.to_dict()
        user_data.update({
            'statistics': {
                'adventures_created': user_adventures,
                'bookings_made': user_bookings,
                'payments_made': user_payments,
                'total_spent': float(total_spent)
            }
        })
        
        return jsonify({'user': user_data}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch user', 'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['PUT'])
@admin_required
def toggle_admin(user_id):
    try:
        # Prevent self-demotion
        current_user_id = session.get('user_id')
        if user_id == current_user_id:
            return jsonify({'message': 'Cannot modify your own admin status'}), 400
        
        user = User.query.get_or_404(user_id)
        user.is_admin = not user.is_admin
        
        db.session.commit()
        
        action = "granted" if user.is_admin else "revoked"
        return jsonify({
            'message': f'Admin privileges {action} successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update admin status', 'error': str(e)}), 500

@admin_bp.route('/adventures', methods=['GET'])
@admin_required
def get_all_adventures():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', 'all')  # all, active, inactive
        
        query = Adventure.query
        
        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)
        
        pagination = query.order_by(Adventure.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
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
        return jsonify({
            'message': f'Adventure {status} successfully',
            'adventure': adventure.to_dict()
        }), 200
        
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
        
        pagination = query.order_by(Booking.created_at.desc()).paginate(
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
        
        return jsonify({
            'message': 'Booking status updated successfully',
            'booking': booking.to_dict()
        }), 200
        
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
        
        pagination = query.order_by(Payment.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
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

@admin_bp.route('/reports/revenue', methods=['GET'])
@admin_required
def revenue_report():
    try:
        period = request.args.get('period', 'monthly')  # daily, weekly, monthly, yearly
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Payment.query.filter(Payment.status == 'completed')
        
        # Date filtering
        if start_date:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Payment.created_at >= start_datetime)
        
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Payment.created_at <= end_datetime)
        
        if period == 'daily':
            revenue_data = db.session.query(
                func.date(Payment.created_at).label('date'),
                func.sum(Payment.amount).label('revenue'),
                func.count(Payment.id).label('transactions')
            ).group_by('date').order_by('date').all()
        elif period == 'weekly':
            revenue_data = db.session.query(
                func.date_trunc('week', Payment.created_at).label('week'),
                func.sum(Payment.amount).label('revenue'),
                func.count(Payment.id).label('transactions')
            ).group_by('week').order_by('week').all()
        elif period == 'monthly':
            revenue_data = db.session.query(
                extract('year', Payment.created_at).label('year'),
                extract('month', Payment.created_at).label('month'),
                func.sum(Payment.amount).label('revenue'),
                func.count(Payment.id).label('transactions')
            ).group_by('year', 'month').order_by('year', 'month').all()
        else:  # yearly
            revenue_data = db.session.query(
                extract('year', Payment.created_at).label('year'),
                func.sum(Payment.amount).label('revenue'),
                func.count(Payment.id).label('transactions')
            ).group_by('year').order_by('year').all()
        
        return jsonify({
            'period': period,
            'revenue_data': [
                {
                    'period': str(getattr(item, period)),
                    'revenue': float(item.revenue),
                    'transactions': item.transactions
                } for item in revenue_data
            ],
            'total_revenue': float(sum(item.revenue for item in revenue_data)),
            'total_transactions': sum(item.transactions for item in revenue_data)
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to generate revenue report', 'error': str(e)}), 500

@admin_bp.route('/reports/bookings', methods=['GET'])
@admin_required
def bookings_report():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Booking.query
        
        if start_date:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Booking.created_at >= start_datetime)
        
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Booking.created_at <= end_datetime)
        
        # Booking status distribution
        status_distribution = db.session.query(
            Booking.status,
            func.count(Booking.id).label('count')
        ).group_by(Booking.status).all()
        
        # Popular adventures
        popular_adventures = db.session.query(
            Adventure.title,
            func.count(Booking.id).label('booking_count')
        ).join(Booking, Adventure.id == Booking.adventure_id
        ).group_by(Adventure.id, Adventure.title
        ).order_by(func.count(Booking.id).desc()
        ).limit(10).all()
        
        # Monthly booking trend
        monthly_trend = db.session.query(
            extract('year', Booking.created_at).label('year'),
            extract('month', Booking.created_at).label('month'),
            func.count(Booking.id).label('booking_count')
        ).group_by('year', 'month').order_by('year', 'month').all()
        
        return jsonify({
            'status_distribution': [
                {'status': status, 'count': count} for status, count in status_distribution
            ],
            'popular_adventures': [
                {'adventure': title, 'booking_count': count} for title, count in popular_adventures
            ],
            'monthly_trend': [
                {
                    'year': int(year),
                    'month': int(month),
                    'booking_count': count
                } for year, month, count in monthly_trend
            ],
            'total_bookings': query.count()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to generate bookings report', 'error': str(e)}), 500