# app/__init__.py
import os
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate, bcrypt, login_manager, cors
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
        SECRET_KEY=os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production',
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
    login_manager.init_app(app)  # ✅ CRITICAL: Initialize Flask-Login
    cors.init_app(app)

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
    
    # Apply CORS configuration
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
        supports_credentials=True
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
    # Test endpoint for bookings API
    # -----------------------------
    @app.route('/api/bookings/test')
    def bookings_test():
        """Test endpoint for bookings API."""
        return jsonify({
            "success": True,
            "message": "Bookings API is working!",
            "timestamp": os.path.getmtime(__file__)
        })

    # -----------------------------
    # Error handlers
    # -----------------------------
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            "success": False,
            "message": "Resource not found",
            "error": str(error)
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "error": str(error) if app.debug else "An internal error occurred"
        }), 500

    @app.errorhandler(401)
    def unauthorized_error(error):
        return jsonify({
            "success": False,
            "message": "Unauthorized access",
            "error": "Please log in to access this resource"
        }), 401

    return app