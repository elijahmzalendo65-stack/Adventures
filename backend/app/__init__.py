# app/__init__.py
import os
from flask import Flask, jsonify, send_from_directory, request
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
    
    # IMPORTANT: Session configuration for authentication
    app.config.update(
        SESSION_COOKIE_SAMESITE='Lax',  # Allows cross-origin cookies
        SESSION_COOKIE_SECURE=False,     # False for local development
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_NAME='mlima_session',
        PERMANENT_SESSION_LIFETIME=86400  # 24 hours
    )

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # -----------------------------
    # CORS Configuration - CRITICAL FIX
    # -----------------------------
    # Your frontend runs on localhost:8080, backend on localhost:5000
    allowed_origins = [
        "http://localhost:8080",        # Frontend dev server
        "http://127.0.0.1:8080",        # Frontend dev server alternative
        "http://localhost:5000",         # Direct backend access
        "http://127.0.0.1:5000",         # Direct backend access
        "https://mlima-adventures.onrender.com",  # Production
    ]
    
    # Initialize CORS with ALL origins that need access
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "supports_credentials": True,
                "allow_headers": [
                    "Content-Type", 
                    "Authorization", 
                    "X-Requested-With", 
                    "Accept",
                    "Origin"
                ],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                "expose_headers": ["Set-Cookie", "Authorization"],
                "max_age": 600
            }
        },
        supports_credentials=True,
        expose_headers=['Set-Cookie']
    )

    # -----------------------------
    # Register Blueprints
    # -----------------------------
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(adventures_bp, url_prefix='/api/adventures')
    app.register_blueprint(mpesa_bp, url_prefix='/api/mpesa')
    app.register_blueprint(booking_bp, url_prefix='/api/bookings')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # -----------------------------
    # After request handler - Ensures CORS headers on ALL responses
    # -----------------------------
    @app.after_request
    def after_request(response):
        """Add CORS headers to all responses."""
        origin = request.headers.get('Origin')
        
        # Check if origin is in allowed list
        if origin and origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        
        # Add other CORS headers
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
        response.headers['Access-Control-Expose-Headers'] = 'Set-Cookie'
        
        return response

    # -----------------------------
    # Health check and root endpoints
    # -----------------------------
    @app.route('/')
    def index():
        """Root endpoint - redirects to health check."""
        return jsonify({
            "message": "Mlima Adventures API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/health",
                "auth": "/api/auth",
                "adventures": "/api/adventures",
                "bookings": "/api/bookings"
            }
        })

    @app.route('/api/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "service": "mlima-adventures-api",
            "database": "connected" if db.engine else "disconnected"
        })

    # -----------------------------
    # Error handlers
    # -----------------------------
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"message": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"message": "Internal server error"}), 500

    return app