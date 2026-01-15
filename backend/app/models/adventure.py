# app/models/adventure.py
from ..extensions import db
from datetime import datetime

class Adventure(db.Model):
    __tablename__ = "adventures"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    duration = db.Column(db.String(100), nullable=False, default="1 day")
    difficulty = db.Column(db.String(50), nullable=False, default="moderate")
    image_url = db.Column(db.String(500), nullable=True)
    max_capacity = db.Column(db.Integer, nullable=False, default=20)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # ✅ FIXED: Use UNIQUE relationship names
    creator = db.relationship("User", backref="user_adventures", lazy=True)
    adventure_bookings = db.relationship("Booking", backref="booking_adventure", lazy=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "price": self.price,
            "duration": self.duration,
            "difficulty": self.difficulty,
            "image_url": self.image_url,
            "max_capacity": self.max_capacity,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f"<Adventure {self.title}>"