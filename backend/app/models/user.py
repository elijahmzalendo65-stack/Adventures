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
    # Use cascade='all, delete-orphan' to delete related objects if user is deleted
    adventures = db.relationship(
        'Adventure', 
        backref='creator', 
        lazy=True, 
        cascade='all, delete-orphan'
    )
    payments = db.relationship(
        'Payment', 
        backref='user', 
        lazy=True, 
        cascade='all, delete-orphan'
    )
    bookings = db.relationship(
        'Booking', 
        backref='user', 
        lazy=True, 
        cascade='all, delete-orphan'
    )

    # -----------------------------
    # Password Handling
    # -----------------------------
    def set_password(self, password: str):
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies the user's password."""
        return check_password_hash(self.password_hash, password)

    # -----------------------------
    # Serialization
    # -----------------------------
    def to_dict(self) -> dict:
        """Returns a dictionary representation of the user."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone_number': self.phone_number,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    # -----------------------------
    # Admin Dashboard Helpers
    # -----------------------------
    @staticmethod
    def get_all_users(search: str = '', page: int = 1, per_page: int = 50):
        """Fetch users with optional search and pagination for admin dashboard."""
        query = User.query
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                db.or_(
                    db.func.lower(User.username).like(search_term),
                    db.func.lower(User.email).like(search_term)
                )
            )
        query = query.order_by(User.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)
