from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # -----------------------------
    # Relationships
    # -----------------------------
    adventures = db.relationship('Adventure', back_populates='creator', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', back_populates='user', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='user', lazy=True, cascade='all, delete-orphan')

    # -----------------------------
    # Password Handling
    # -----------------------------
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # -----------------------------
    # Serialization
    # -----------------------------
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone_number': self.phone_number,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'adventures_count': len(self.adventures),
            'bookings_count': len(self.bookings),
            'payments_count': len(self.payments)
        }
