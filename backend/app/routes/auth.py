# app/routes/auth.py
from flask import Blueprint, request, jsonify, session
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.user import User
from ..utils.helpers import login_required, admin_required, validate_required_fields
from sqlalchemy import or_

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ----------------------------
# REGISTER (FIXED - NO to_dict())
# ----------------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user and automatically log them in."""
    try:
        data = request.get_json() or {}

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

        # ✅ FIXED: Return SIMPLE dictionary, NOT user.to_dict()
        return jsonify({
            "message": "Registration successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "User already exists"}), 400

    except Exception as e:
        db.session.rollback()
        # ✅ FIXED: Return simple error without exposing details
        return jsonify({"message": "Registration failed"}), 500


# ----------------------------
# LOGIN (FIXED - Removed hardcoded "admin456")
# ----------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login using email OR username (case-insensitive for email).
    Session-based auth, admin supported.
    """
    try:
        data = request.get_json() or {}
        identifier = data.get("email") or data.get("username")
        password = data.get("password")

        if not identifier or not password:
            return jsonify({"message": "Email/Username and password are required"}), 400

        identifier = identifier.strip()
        email_identifier = identifier.lower()

        # ✅ FIXED: Search by ACTUAL user input, not hardcoded "admin456"
        user = User.query.filter(
            or_(
                User.email == email_identifier,
                User.username == identifier
            )
        ).first()

        if not user or not user.check_password(password):
            return jsonify({"message": "Invalid credentials"}), 401

        # Login successful, start session
        session.clear()
        session["user_id"] = user.id
        session.permanent = True

        # ✅ FIXED: Return SIMPLE dictionary
        return jsonify({
            "message": "Login successful",
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
        return jsonify({"message": "Login failed"}), 500


# ----------------------------
# LOGOUT
# ----------------------------
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


# ----------------------------
# CHECK AUTH (FIXED - NO to_dict())
# ----------------------------
@auth_bp.route("/check-auth", methods=["GET"])
def check_auth():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 200

    user = User.query.get(user_id)
    if not user:
        session.clear()
        return jsonify({"authenticated": False}), 200

    # ✅ FIXED: Return SIMPLE dictionary
    return jsonify({
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    }), 200


# ----------------------------
# CURRENT USER PROFILE (FIXED - NO to_dict())
# ----------------------------
@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    user = User.query.get(session["user_id"])
    # ✅ FIXED: Return SIMPLE dictionary
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


# ----------------------------
# ADMIN – VIEW ALL USERS (FIXED - NO to_dict())
# ----------------------------
@auth_bp.route("/admin/users", methods=["GET"])
@admin_required
def admin_get_users():
    """
    Used by Admin Dashboard.
    Returns all registered users.
    """
    users = User.query.order_by(User.created_at.desc()).all()

    # ✅ FIXED: Return SIMPLE dictionaries
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

    return jsonify({
        "users": users_data
    }), 200


# ----------------------------
# EMERGENCY REGISTRATION ENDPOINT
# ----------------------------
@auth_bp.route("/register-simple", methods=["POST"])
def register_simple():
    """
    EMERGENCY registration endpoint that uses DIRECT SQL.
    Bypasses all ORM relationship issues.
    """
    try:
        data = request.get_json() or {}
        
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        phone_number = data.get("phone_number") or ""
        
        if not username or not email or not password:
            return jsonify({"message": "Username, email and password are required"}), 400
        
        # DIRECT SQL - bypass ORM completely
        from sqlalchemy import text
        from werkzeug.security import generate_password_hash
        
        # 1. Check if user exists
        check_sql = text("SELECT id FROM users WHERE username = :u OR email = :e")
        existing = db.session.execute(check_sql, {"u": username, "e": email}).fetchone()
        
        if existing:
            return jsonify({"message": "Username or email already exists"}), 400
        
        # 2. Create user with DIRECT SQL
        password_hash = generate_password_hash(password)
        
        insert_sql = text("""
            INSERT INTO users (username, email, password_hash, phone_number, created_at, updated_at)
            VALUES (:username, :email, :password_hash, :phone, NOW(), NOW())
            RETURNING id, username, email, phone_number, is_admin, created_at
        """)
        
        result = db.session.execute(insert_sql, {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "phone": phone_number
        })
        db.session.commit()
        
        user_data = result.fetchone()
        
        # 3. Create session
        session.clear()
        session["user_id"] = user_data.id
        session.permanent = True
        
        return jsonify({
            "message": "Registration successful!",
            "user": {
                "id": user_data.id,
                "username": user_data.username,
                "email": user_data.email,
                "phone_number": user_data.phone_number,
                "is_admin": user_data.is_admin,
                "created_at": user_data.created_at.isoformat() if user_data.created_at else None,
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Registration failed. Please try again."}), 500