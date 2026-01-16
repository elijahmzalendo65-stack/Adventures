# app/models/user.py - UPDATED WITH FLASK-LOGIN SUPPORT
from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)  # Required for Flask-Login
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - COMMENTED OUT to prevent errors
    # bookings = db.relationship("Booking", backref="booking_user", lazy=True)
    
    # Flask-Login methods (provided by UserMixin):
    # - is_authenticated: Returns True if user is authenticated
    # - is_active: Returns True if user account is active
    # - is_anonymous: Returns False for regular users
    # - get_id: Returns the user ID as string
    
    def set_password(self, password: str):
        """Hash and set the password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if password matches hash."""
        try:
            return check_password_hash(self.password_hash, password)
        except Exception:
            return False
    
    # Additional properties for compatibility
    @property
    def is_authenticated(self):
        """Override if needed - default from UserMixin is usually fine."""
        return True
    
    @property
    def is_active(self):
        """Check if user account is active."""
        return self._is_active if hasattr(self, '_is_active') else True
    
    @is_active.setter
    def is_active(self, value):
        """Set active status."""
        self._is_active = value
    
    def get_id(self):
        """Return user ID as string (required by Flask-Login)."""
        return str(self.id)
    
    def to_dict(self):
        """Safe serialization - avoid circular references."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone_number": self.phone_number,
            "is_admin": bool(self.is_admin),
            "is_active": bool(self.is_active) if hasattr(self, 'is_active') else True,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @staticmethod
    def get_by_id(user_id):
        """Static method to get user by ID."""
        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def get_by_username(username):
        """Static method to get user by username."""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_by_email(email):
        """Static method to get user by email."""
        return User.query.filter_by(email=email).first()
    
    def __repr__(self):
        return f"<User {self.username} ({self.id})>"