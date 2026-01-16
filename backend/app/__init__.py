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
    # Get the backend directory
    backend_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Go up one level to project root, then into frontend/dist
    project_root = os.path.dirname(backend_dir)  # Go up from backend
    static_folder = os.path.join(project_root, 'frontend', 'dist')
    
    # If dist doesn't exist, try build folder
    if not os.path.exists(static_folder):
        static_folder = os.path.join(project_root, 'frontend', 'build')
    
    print(f"🎯 Project root: {project_root}")
    print(f"🎯 Setting static folder to: {static_folder}")
    print(f"🎯 Static folder exists: {os.path.exists(static_folder)}")
    
    # If static folder doesn't exist, provide helpful message
    if not os.path.exists(static_folder):
        print(f"❌ Static folder not found!")
        print(f"   Please build your React app:")
        print(f"   cd {os.path.join(project_root, 'frontend')} && npm run build")
        
        # Create a temporary static folder to avoid Flask errors
        os.makedirs(static_folder, exist_ok=True)
        with open(os.path.join(static_folder, 'index.html'), 'w') as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Mlima Adventures - Please Build React App</title>
            </head>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h1>React Frontend Not Built</h1>
                <p>Please build your React app first:</p>
                <pre style="background: #f0f0f0; padding: 10px; border-radius: 5px;">
cd frontend && npm run build
                </pre>
                <p>Or check that your static folder is configured correctly.</p>
                <p>Expected static folder at: <code>{}</code></p>
            </body>
            </html>
            """.format(static_folder))
    
    # Initialize Flask with static folder
    app = Flask(__name__, 
                static_folder=static_folder,
                static_url_path='')
    
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
    # Add localhost:5000 to allowed origins since we're serving frontend from same origin
    allowed_origins = [
        "http://localhost:8080",        # Frontend dev server
        "http://127.0.0.1:8080",        # Frontend dev server alternative
        "http://localhost:5000",         # Backend serving frontend
        "http://127.0.0.1:5000",         # Backend serving frontend
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
    # Add this: Serve React frontend for all non-API routes
    # -----------------------------
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve React frontend for all non-API routes."""
        # Don't interfere with API routes
        if path.startswith('api/'):
            return jsonify({"error": "API route not found"}), 404
        
        # Check if the requested file exists
        static_file_path = os.path.join(app.static_folder, path)
        
        if path and os.path.exists(static_file_path):
            print(f"📁 Serving static file: {path}")
            return send_from_directory(app.static_folder, path)
        
        # Serve index.html for all other routes (React Router will handle it)
        print(f"📄 Serving index.html for path: {path}")
        return send_from_directory(app.static_folder, 'index.html')

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