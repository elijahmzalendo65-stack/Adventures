# app/models/payment.py
from ..extensions import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = "payments"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    adventure_id = db.Column(db.Integer, db.ForeignKey('adventures.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    
    mpesa_receipt_number = db.Column(db.String(50), nullable=True)
    phone_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False, default='pending')
    checkout_request_id = db.Column(db.String(100), nullable=True)
    merchant_request_id = db.Column(db.String(100), nullable=True)
    result_code = db.Column(db.String(10), nullable=True)
    result_desc = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # ✅ FIXED: Simple backrefs
    user = db.relationship("User", backref="user_payments", lazy=True)
    adventure = db.relationship("Adventure", backref="adventure_payments", lazy=True)
    booking = db.relationship("Booking", backref="booking_payment", lazy=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "adventure_id": self.adventure_id,
            "booking_id": self.booking_id,
            "mpesa_receipt_number": self.mpesa_receipt_number,
            "phone_number": self.phone_number,
            "amount": self.amount,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f"<Payment {self.id}: KES {self.amount} ({self.status})>"