from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models.user import User
from ..utils.helpers import login_required, admin_required, validate_required_fields

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user and immediately return updated admin user list."""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["username", "email", "password"]
        is_valid, error_message = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({"message": error_message}), 400

        # Check if username or email already exists
        if User.query.filter_by(username=data.get("username")).first():
            return jsonify({"message": "Username already exists"}), 400
        if User.query.filter_by(email=data.get("email")).first():
            return jsonify({"message": "Email already exists"}), 400

        # Create new user
        user = User(
            username=data.get("username"),
            email=data.get("email"),
            phone_number=data.get("phone_number"),
        )
        user.set_password(data.get("password"))

        db.session.add(user)
        db.session.commit()

        # Log in the user via session
        session["user_id"] = user.id
        session.permanent = True

        # Fetch updated users list for admin dashboard
        users = User.get_all_users(page=1, per_page=50)

        return jsonify({
            "message": "User created successfully",
            "user": user.to_dict(),
            "admin_users": [u.to_dict() for u in users.items],
            "total_users": users.total,
            "total_pages": users.pages
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Registration failed", "error": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """Log in a user using username and password."""
    try:
        data = request.get_json()
        if not data.get("username") or not data.get("password"):
            return jsonify({"message": "Username and password are required"}), 400

        user = User.query.filter_by(username=data.get("username")).first()

        if user and user.check_password(data.get("password")):
            session["user_id"] = user.id
            session.permanent = True
            return jsonify({"message": "Login successful", "user": user.to_dict()}), 200

        return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"message": "Login failed", "error": str(e)}), 500


@auth_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    """Return the currently logged-in user's profile."""
    user_id = session.get("user_id")
    user = User.query.get(user_id)
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Log out the current user."""
    session.pop("user_id", None)
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/check-auth", methods=["GET"])
def check_auth():
    """Check if a user is currently authenticated."""
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        return jsonify({"authenticated": True, "user": user.to_dict()}), 200
    return jsonify({"authenticated": False}), 200


# ------------------------------
# Admin Routes
# ------------------------------
@auth_bp.route("/admin/users", methods=["GET"])
@admin_required
def get_all_users():
    """Return all users for the admin dashboard with optional search."""
    search = request.args.get("search", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    users = User.get_all_users(search=search, page=page, per_page=per_page)
    return jsonify({
        "users": [user.to_dict() for user in users.items],
        "total": users.total,
        "pages": users.pages,
        "current_page": users.page
    }), 200
