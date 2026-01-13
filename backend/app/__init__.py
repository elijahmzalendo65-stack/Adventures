# app/__init__.py
import os
from flask import Flask, jsonify, send_from_directory
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
    base_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dist = os.path.join(base_dir, "../../frontend/dist")
    app = Flask(
        __name__,
    static_folder= frontend_dist ,
    static_url_path=""
)




    app.config.from_object(config_class)

    
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    
    CORS(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": ["https://mlima-adventures.onrender.com","http://localhost:8080"]
        }},
    )


    # -----------------------------
    # Register Blueprints
    # -----------------------------
    app.register_blueprint(auth_bp)  # /api/auth
    app.register_blueprint(adventures_bp)  # /api/adventures
    app.register_blueprint(mpesa_bp)  # /api/mpesa
    app.register_blueprint(booking_bp)  # /api/bookings
    app.register_blueprint(admin_bp)  # /api/admin

  
    
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
