from flask import Flask
from flask_cors import CORS
from config import Config
from app.extensions import db, migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.adventures import adventures_bp
    from app.routes.mpesa import mpesa_bp
    from app.routes.booking import booking_bp
    from app.routes.admin import admin_bp  # NEW

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(adventures_bp, url_prefix='/api/adventures')
    app.register_blueprint(mpesa_bp, url_prefix='/api/mpesa')
    app.register_blueprint(booking_bp, url_prefix='/api/bookings')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')  # NEW

    return app