from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models.user import User
from app.utils.helpers import login_required, admin_required, validate_required_fields

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['username', 'email', 'password']
        is_valid, error_message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({'message': error_message}), 400
        
        if User.query.filter_by(username=data.get('username')).first():
            return jsonify({'message': 'Username already exists'}), 400
            
        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'message': 'Email already exists'}), 400
            
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            phone_number=data.get('phone_number')
        )
        user.set_password(data.get('password'))
        
        db.session.add(user)
        db.session.commit()
        
        # Log the user in after registration
        session['user_id'] = user.id
        session.permanent = True
        
        return jsonify({
            'message': 'User created successfully', 
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Username and password are required'}), 400
            
        user = User.query.filter_by(username=data.get('username')).first()
        
        if user and user.check_password(data.get('password')):
            session['user_id'] = user.id
            session.permanent = True
            
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict()
            }), 200
            
        return jsonify({'message': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    return jsonify({'user': user.to_dict()}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        return jsonify({'authenticated': True, 'user': user.to_dict()}), 200
    return jsonify({'authenticated': False}), 200

@auth_bp.route('/check-admin', methods=['GET'])
@login_required
def check_admin():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    return jsonify({'is_admin': user.is_admin}), 200