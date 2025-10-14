

from ..extensions import db
from datetime import datetime
import secrets, string

class Booking(db.Model):
    __tablename__ = 'bookings'

    
    id = db.Column(db.Integer, primary_key=True)


    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    adventure_id = db.Column(db.Integer, db.ForeignKey('adventures.id'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)

    
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    adventure_date = db.Column(db.DateTime, nullable=False)
    number_of_people = db.Column(db.Integer, nullable=False, default=1)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    special_requests = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, cancelled, completed
    booking_reference = db.Column(db.String(100), unique=True, nullable=False)

    
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)

    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    
    user = db.relationship('User', back_populates='bookings', lazy=True)
    adventure = db.relationship('Adventure', back_populates='bookings', lazy=True)
    payment_rel = db.relationship('Payment', back_populates='booking', lazy=True, uselist=False)

    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        if not self.total_amount:
            self.calculate_total_amount()

   
    def generate_booking_reference(self) -> str:
        """Generate a unique booking reference."""
        characters = string.ascii_uppercase + string.digits
        return 'BK' + ''.join(secrets.choice(characters) for _ in range(8))

    def calculate_total_amount(self) -> float:
        """Calculate total amount based on adventure price and number of people."""
        if self.adventure:
            self.total_amount = self.adventure.price * self.number_of_people
        return self.total_amount

    
    def to_dict(self) -> dict:
        """Return a dictionary representation including related objects."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'adventure_id': self.adventure_id,
            'payment_id': self.payment_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'adventure_date': self.adventure_date.isoformat() if self.adventure_date else None,
            'number_of_people': self.number_of_people,
            'total_amount': self.total_amount,
            'special_requests': self.special_requests,
            'status': self.status,
            'booking_reference': self.booking_reference,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': self.user.to_dict() if self.user else None,
            'adventure': self.adventure.to_dict() if self.adventure else None,
            'payment': self.payment_rel.to_dict() if self.payment_rel else None
        }
