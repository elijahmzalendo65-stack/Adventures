from flask import Blueprint, request, jsonify, session
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.user import User
from ..utils.helpers import login_required, admin_required, validate_required_fields

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ----------------------------
# REGISTER
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

        if User.query.filter_by(username=username).first():
            return jsonify({"message": "Username already exists"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"message": "Email already exists"}), 400

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

        return jsonify({
            "message": "Registration successful",
            "user": user.to_dict()
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "User already exists"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Registration failed", "error": str(e)}), 500


# ----------------------------
# LOGIN
# ----------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login using email OR username.
    Admin login supported.
    """
    try:
        data = request.get_json() or {}
        identifier = data.get("email") or data.get("username")
        password = data.get("password")

        if not identifier or not password:
            return jsonify({"message": "Email/Username and password are required"}), 400

        identifier = identifier.strip().lower()

        user = User.query.filter(
            (User.email == identifier) | (User.username == identifier)
        ).first()

        if not user or not user.check_password(password):
            return jsonify({"message": "Invalid credentials"}), 401

        session.clear()
        session["user_id"] = user.id
        session.permanent = True

        return jsonify({
            "message": "Login successful",
            "user": user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({"message": "Login failed", "error": str(e)}), 500


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


# ----------------------------
# CHECK AUTH
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

    return jsonify({
        "authenticated": True,
        "user": user.to_dict()
    }), 200


# ----------------------------
# CURRENT USER PROFILE
# ----------------------------
@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    user = User.query.get(session["user_id"])
    return jsonify({"user": user.to_dict()}), 200


# ----------------------------
# ADMIN – VIEW ALL USERS
# ----------------------------
@auth_bp.route("/admin/users", methods=["GET"])
@admin_required
def admin_get_users():
    """
    Used by Admin Dashboard.
    Returns all registered users.
    """
    users = User.query.order_by(User.created_at.desc()).all()

    return jsonify({
        "users": [user.to_dict() for user in users]
    }), 200
