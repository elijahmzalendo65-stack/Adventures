# app/routes/auth.py

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

        # ✅ Validate required fields
        required_fields = ["username", "email", "password"]
        is_valid, error_message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({"message": error_message}), 400

        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password")
        phone_number = data.get("phone_number", "").strip() or None

        # ✅ Check if username or email already exists
        if User.query.filter_by(username=username).first():
            return jsonify({"message": "Username already exists"}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({"message": "Email already exists"}), 400

        # ✅ Create user and hash password
        user = User(username=username, email=email, phone_number=phone_number)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # ✅ Start user session
        session.clear()
        session["user_id"] = user.id
        session.permanent = True

        return jsonify({
            "message": "User registered successfully",
            "user": user.to_dict()
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "User with given credentials already exists"}), 400

    except Exception as e:
        db.session.rollback()
        print("Registration Error:", str(e))
        return jsonify({"message": "Registration failed", "error": str(e)}), 500


# ----------------------------
# LOGIN
# ----------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    """Log in a user using username or email and password."""
    try:
        data = request.get_json() or {}
        identifier = data.get("username", "").strip()
        password = data.get("password")

        if not identifier or not password:
            return jsonify({"message": "Username/Email and password are required"}), 400

        # ✅ Support login with either username or email
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if not user or not user.check_password(password):
            return jsonify({"message": "Invalid credentials"}), 401

        # ✅ Set session
        session.clear()
        session["user_id"] = user.id
        session.permanent = True

        return jsonify({
            "message": "Login successful",
            "user": user.to_dict()
        }), 200

    except Exception as e:
        print("Login Error:", str(e))
        return jsonify({"message": "Login failed", "error": str(e)}), 500


# ----------------------------
# LOGOUT
# ----------------------------
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Log out the current user."""
    session.pop("user_id", None)
    return jsonify({"message": "Logged out successfully"}), 200


# ----------------------------
# CHECK AUTH
# ----------------------------
@auth_bp.route("/check-auth", methods=["GET"])
def check_auth():
    """Check if a user is currently authenticated."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 200

    user = User.query.get(user_id)
    if not user:
        session.pop("user_id", None)
        return jsonify({"authenticated": False}), 200

    return jsonify({
        "authenticated": True,
        "user": user.to_dict()
    }), 200


# ----------------------------
# PROFILE (CURRENT USER)
# ----------------------------
@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """Return the current logged-in user's profile."""
    user_id = session.get("user_id")
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({"user": user.to_dict()}), 200


# ----------------------------
# ADMIN - VIEW USERS
# ----------------------------
@auth_bp.route("/admin/users", methods=["GET"])
@admin_required
def get_all_users():
    """Return all users for the admin dashboard with optional search & pagination."""
    search = request.args.get("search", "").strip()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )

    users = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "users": [user.to_dict() for user in users.items],
        "total": users.total,
        "pages": users.pages,
        "current_page": users.page
    }), 200
