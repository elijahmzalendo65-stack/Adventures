from ..extensions import db
from datetime import datetime

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    adventure_id = db.Column(db.Integer, db.ForeignKey('adventures.id'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)
    
    # Booking details
    booking_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    adventure_date = db.Column(db.DateTime, nullable=False)
    number_of_people = db.Column(db.Integer, nullable=False, default=1)
    total_amount = db.Column(db.Float, nullable=False)
    special_requests = db.Column(db.Text)
    
    # Booking status
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, cancelled, completed
    booking_reference = db.Column(db.String(100), unique=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def __init__(self, **kwargs):
        super(Booking, self).__init__(**kwargs)
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        if not self.total_amount and hasattr(self, 'adventure'):
            self.calculate_total_amount()
    
    def generate_booking_reference(self):
        import secrets
        import string
        characters = string.ascii_uppercase + string.digits
        return 'BK' + ''.join(secrets.choice(characters) for _ in range(8))
    
    def calculate_total_amount(self):
        """Calculate total amount based on adventure price and number of people"""
        if hasattr(self, 'adventure') and self.adventure:
            self.total_amount = self.adventure.price * self.number_of_people
        return self.total_amount
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'adventure_id': self.adventure_id,
            'payment_id': self.payment_id,
            'booking_date': self.booking_date.isoformat(),
            'adventure_date': self.adventure_date.isoformat(),
            'number_of_people': self.number_of_people,
            'total_amount': self.total_amount,
            'special_requests': self.special_requests,
            'status': self.status,
            'booking_reference': self.booking_reference,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user': self.user.to_dict() if self.user else None,
            'adventure': self.adventure.to_dict() if self.adventure else None,
            'payment': self.payment_rel.to_dict() if self.payment_rel else None
        }