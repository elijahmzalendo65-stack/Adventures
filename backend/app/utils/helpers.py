from functools import wraps
from flask import session, jsonify
from app.models.user import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'message': 'Authentication required'}), 401
        
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'message': 'Admin access required'}), 403
            
        return f(*args, **kwargs)
    return decorated_function

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present in the data"""
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    return True, None