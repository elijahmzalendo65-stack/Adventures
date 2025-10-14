from ..extensions import db
from datetime import datetime

class Adventure(db.Model):
    __tablename__ = 'adventures'

    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False, default=0.0)
    duration = db.Column(db.String(100))
    difficulty = db.Column(db.String(50))
    image_url = db.Column(db.String(500))
    max_capacity = db.Column(db.Integer, default=10)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

   
    creator = db.relationship('User', back_populates='adventures', lazy=True)
    bookings = db.relationship(
        'Booking',
        back_populates='adventure',
        lazy=True,
        cascade='all, delete-orphan'
    )
    payments = db.relationship(
        'Payment',
        back_populates='adventure',
        lazy=True,
        cascade='all, delete-orphan'
    )

    
    def calculate_available_slots(self, date: datetime = None) -> int:
        """
        Calculate available slots for a specific date.
        Defaults to current date if not provided.
        """
        from ..models.booking import Booking  
        if not date:
            date = datetime.utcnow()
        confirmed_count = Booking.query.filter(
            Booking.adventure_id == self.id,
            db.func.date(Booking.adventure_date) == date.date(),
            Booking.status == 'confirmed'
        ).count()
        return max(self.max_capacity - confirmed_count, 0)

    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'price': self.price,
            'duration': self.duration,
            'difficulty': self.difficulty,
            'image_url': self.image_url,
            'max_capacity': self.max_capacity,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user_id': self.user_id,
            'creator_username': self.creator.username if self.creator else None,
            'bookings_count': len(self.bookings),
            'payments_count': len(self.payments),
            'available_slots': self.calculate_available_slots()
        }
