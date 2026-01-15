# app/models/booking.py
from ..extensions import db
from datetime import datetime
import secrets
import string

class Booking(db.Model):
    __tablename__ = "bookings"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    adventure_id = db.Column(db.Integer, db.ForeignKey("adventures.id"), nullable=False)
    
    booking_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    adventure_date = db.Column(db.DateTime, nullable=False)
    number_of_people = db.Column(db.Integer, nullable=False, default=1)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    special_requests = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="pending")
    booking_reference = db.Column(db.String(100), unique=True, nullable=False)
    
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ✅ FIXED: Use simple backrefs with UNIQUE names
    user = db.relationship("User", backref="user_bookings", lazy=True)
    # ⚠️ NO adventure relationship here - it's defined in Adventure model
    
    def __init__(self, **kwargs):
        if not kwargs.get("booking_reference"):
            kwargs["booking_reference"] = self.generate_booking_reference()
        super().__init__(**kwargs)
    
    @staticmethod
    def generate_booking_reference():
        chars = string.ascii_uppercase + string.digits
        return "BK-" + "".join(secrets.choice(chars) for _ in range(8))
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "adventure_id": self.adventure_id,
            "booking_date": self.booking_date.isoformat() if self.booking_date else None,
            "adventure_date": self.adventure_date.isoformat() if self.adventure_date else None,
            "number_of_people": self.number_of_people,
            "total_amount": self.total_amount,
            "special_requests": self.special_requests,
            "status": self.status,
            "booking_reference": self.booking_reference,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Booking {self.booking_reference}: {self.status}>"