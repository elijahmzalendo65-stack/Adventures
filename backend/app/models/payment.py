

from ..extensions import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'

    
    id = db.Column(db.Integer, primary_key=True)

    
    mpesa_receipt_number = db.Column(db.String(50), nullable=True)
    phone_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed
    checkout_request_id = db.Column(db.String(100), nullable=True)
    merchant_request_id = db.Column(db.String(100), nullable=True)
    result_code = db.Column(db.Integer, nullable=True)
    result_desc = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    adventure_id = db.Column(db.Integer, db.ForeignKey('adventures.id'), nullable=False)

   
    user = db.relationship('User', back_populates='payments', lazy=True)
    adventure = db.relationship('Adventure', back_populates='payments', lazy=True)
    booking = db.relationship('Booking', back_populates='payment_rel', uselist=False, lazy=True)

   
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'mpesa_receipt_number': self.mpesa_receipt_number,
            'phone_number': self.phone_number,
            'amount': self.amount,
            'status': self.status,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'checkout_request_id': self.checkout_request_id,
            'merchant_request_id': self.merchant_request_id,
            'result_code': self.result_code,
            'result_desc': self.result_desc,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user_id': self.user_id,
            'user_username': self.user.username if self.user else None,
            'adventure_id': self.adventure_id,
            'adventure_title': self.adventure.title if self.adventure else None,
            'booking_id': self.booking.id if self.booking else None
        }
