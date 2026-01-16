# app/routes/auth.py
from flask import Blueprint, request, jsonify, session, make_response
from sqlalchemy.exc import IntegrityError
from flask_cors import cross_origin
from ..extensions import db
from ..models.user import User
from ..utils.helpers import login_required, admin_required, validate_required_fields
from sqlalchemy import or_
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def add_cors_headers(response):
    """Add CORS headers to response."""
    origin = request.headers.get('Origin')
    allowed_origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080", 
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "https://mlima-adventures.onrender.com"
    ]
    
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
    response.headers['Access-Control-Expose-Headers'] = 'Set-Cookie'
    return response


# ----------------------------
# OPTIONS HANDLER FOR CORS PREFLIGHT
# ----------------------------
@auth_bp.route("/register", methods=["OPTIONS"])
@auth_bp.route("/login", methods=["OPTIONS"])
@auth_bp.route("/logout", methods=["OPTIONS"])
@auth_bp.route("/check-auth", methods=["OPTIONS"])
@auth_bp.route("/me", methods=["OPTIONS"])
def handle_options():
    """Handle CORS preflight requests."""
    logger.debug(f"OPTIONS request for {request.path}")
    response = make_response()
    return add_cors_headers(response)


# ----------------------------
# REGISTER
# ----------------------------
@auth_bp.route("/register", methods=["POST"])
@cross_origin(supports_credentials=True, origins=["http://localhost:8080", "http://127.0.0.1:8080"])
def register():
    """Register a new user and automatically log them in."""
    logger.debug(f"Register request from origin: {request.headers.get('Origin')}")
    
    try:
        data = request.get_json() or {}
        logger.debug(f"Register data: {data}")

        required_fields = ["username", "email", "password"]
        is_valid, error_message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({"message": error_message}), 400

        username = data["username"].strip()
        email = data["email"].strip().lower()
        password = data["password"]
        phone_number = data.get("phone_number")

        # Check for existing username/email
        if User.query.filter_by(username=username).first():
            return jsonify({"message": "Username already exists"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"message": "Email already exists"}), 400

        # Create user
        user = User(
            username=username,
            email=email,
            phone_number=phone_number
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Start session
        session.clear()
        session["user_id"] = user.id
        session.permanent = True
        
        logger.debug(f"User {user.id} registered and session set")

        # Return response with CORS headers
        response_data = {
            "message": "Registration successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        }
        
        response = jsonify(response_data)
        response.status_code = 201
        return add_cors_headers(response)

    except IntegrityError:
        db.session.rollback()
        logger.error("Integrity error during registration")
        return jsonify({"message": "User already exists"}), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration failed: {str(e)}")
        return jsonify({"message": "Registration failed"}), 500


# ----------------------------
# LOGIN
# ----------------------------
@auth_bp.route("/login", methods=["POST"])
@cross_origin(supports_credentials=True, origins=["http://localhost:8080", "http://127.0.0.1:8080"])
def login():
    """
    Login using email OR username (case-insensitive for email).
    Session-based auth, admin supported.
    """
    logger.debug(f"Login request from origin: {request.headers.get('Origin')}")
    
    try:
        data = request.get_json() or {}
        logger.debug(f"Login data: {data}")
        
        identifier = data.get("email") or data.get("username")
        password = data.get("password")

        if not identifier or not password:
            return jsonify({"message": "Email/Username and password are required"}), 400

        identifier = identifier.strip()
        email_identifier = identifier.lower()

        # Search user
        user = User.query.filter(
            or_(
                User.email == email_identifier,
                User.username == identifier
            )
        ).first()

        if not user or not user.check_password(password):
            logger.warning(f"Failed login attempt for: {identifier}")
            return jsonify({"message": "Invalid credentials"}), 401

        # Login successful, start session
        session.clear()
        session["user_id"] = user.id
        session.permanent = True
        
        logger.debug(f"User {user.id} logged in, session: {session}")

        # Return response
        response_data = {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        }
        
        response = jsonify(response_data)
        response.status_code = 200
        return add_cors_headers(response)

    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return jsonify({"message": "Login failed"}), 500


# ----------------------------
# LOGOUT
# ----------------------------
@auth_bp.route("/logout", methods=["POST"])
@login_required
@cross_origin(supports_credentials=True)
def logout():
    """Logout user by clearing session."""
    user_id = session.get("user_id")
    logger.debug(f"Logout request from user {user_id}")
    
    session.clear()
    
    response = jsonify({"message": "Logged out successfully"})
    return add_cors_headers(response)


# ----------------------------
# CHECK AUTH
# ----------------------------
@auth_bp.route("/check-auth", methods=["GET"])
@cross_origin(supports_credentials=True, origins=["http://localhost:8080", "http://127.0.0.1:8080"])
def check_auth():
    """Check if user is authenticated."""
    user_id = session.get("user_id")
    logger.debug(f"Check-auth request, session user_id: {user_id}")
    
    if not user_id:
        response = jsonify({"authenticated": False})
        return add_cors_headers(response)

    user = User.query.get(user_id)
    if not user:
        session.clear()
        response = jsonify({"authenticated": False})
        return add_cors_headers(response)

    # Return authenticated user
    response_data = {
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    }
    
    response = jsonify(response_data)
    return add_cors_headers(response)


# ----------------------------
# CURRENT USER PROFILE
# ----------------------------
@auth_bp.route("/me", methods=["GET"])
@login_required
@cross_origin(supports_credentials=True)
def get_current_user():
    """Get current user profile."""
    user = User.query.get(session["user_id"])
    
    response_data = {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    }
    
    response = jsonify(response_data)
    return add_cors_headers(response)


# ----------------------------
# ADMIN – VIEW ALL USERS
# ----------------------------
@auth_bp.route("/admin/users", methods=["GET"])
@admin_required
@cross_origin(supports_credentials=True)
def admin_get_users():
    """
    Used by Admin Dashboard.
    Returns all registered users.
    """
    users = User.query.order_by(User.created_at.desc()).all()

    users_data = []
    for user in users:
        users_data.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })

    response_data = {"users": users_data}
    response = jsonify(response_data)
    return add_cors_headers(response)


# ----------------------------
# SIMPLE HEALTH CHECK
# ----------------------------
@auth_bp.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    response = jsonify({
        "status": "healthy",
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat()
    })
    return add_cors_headers(response)


# ----------------------------
# SESSION DEBUG ENDPOINT (Remove in production)
# ----------------------------
@auth_bp.route("/debug-session", methods=["GET"])
def debug_session():
    """Debug endpoint to check session state."""
    debug_info = {
        "session_id": session.get("_id", "No session ID"),
        "user_id": session.get("user_id"),
        "session_permanent": session.permanent,
        "session_keys": list(session.keys()),
        "request_origin": request.headers.get("Origin"),
        "request_cookies": dict(request.cookies)
    }
    
    logger.debug(f"Session debug: {debug_info}")
    
    response = jsonify(debug_info)
    return add_cors_headers(response)