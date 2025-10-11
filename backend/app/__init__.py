# app/__init__.py

from flask import Flask, jsonify
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate, bcrypt
from .routes.auth import auth_bp
from .routes.adventures import adventures_bp
from .routes.mpesa import mpesa_bp
from .routes.booking import booking_bp
from .routes.admin import admin_bp


def create_app(config_class=Config):
    """
    Flask application factory.
    Initializes the app, extensions, blueprints, and CORS.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # -----------------------------
    # Initialize extensions
    # -----------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # -----------------------------
    # Enable CORS
    # -----------------------------
    CORS(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": "http://localhost:8081"}}
    )

    # -----------------------------
    # Register blueprints
    # -----------------------------
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(adventures_bp, url_prefix="/api/adventures")
    app.register_blueprint(mpesa_bp, url_prefix="/api/mpesa")
    app.register_blueprint(booking_bp, url_prefix="/api/bookings")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # -----------------------------
    # Root route for testing
    # -----------------------------
    @app.route("/")
    def index():
        return jsonify({"message": "Welcome to Coffee & Adventures API"})

    # -----------------------------
    # Error handlers
    # -----------------------------
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"message": "Resource not found", "error": str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()  # Rollback in case of db errors
        return jsonify({"message": "Internal server error", "error": str(error)}), 500

    return app
