# app/models/user.py

from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"

    # -----------------------------
    # Columns
    # -----------------------------
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
    adventures = db.relationship(
        "Adventure",
        back_populates="creator",
        lazy=True,
        cascade="all, delete-orphan"
    )

    bookings = db.relationship(
        "Booking",
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    payments = db.relationship(
        "Payment",
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # -----------------------------
    # Password Methods
    # -----------------------------
    def set_password(self, password: str):
        """Hash and set the user's password."""
        if not password:
            raise ValueError("Password cannot be empty.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the user's password."""
        return check_password_hash(self.password_hash, password)

    # -----------------------------
    # Serialization
    # -----------------------------
    def to_dict(self) -> dict:
        """Return a dictionary representation of the user."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone_number": self.phone_number,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "adventures_count": len(self.adventures),
            "bookings_count": len(self.bookings),
            "payments_count": len(self.payments),
        }

    # -----------------------------
    # Admin & Utility Methods
    # -----------------------------
    def is_admin_user(self) -> bool:
        """Check if the user has admin privileges."""
        return bool(self.is_admin)

    def active_bookings(self):
        """Return all bookings that are pending or confirmed."""
        return [b for b in self.bookings if b.status in ["pending", "confirmed"]]

    @classmethod
    def get_all_users(cls, search=None, page=1, per_page=50):
        """Return paginated list of all users, with optional search."""
        query = cls.query
        if search:
            query = query.filter(
                db.or_(
                    cls.username.ilike(f"%{search}%"),
                    cls.email.ilike(f"%{search}%"),
                    cls.phone_number.ilike(f"%{search}%")
                )
            )
        return query.order_by(cls.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def __repr__(self):
        return f"<User {self.username}>"
