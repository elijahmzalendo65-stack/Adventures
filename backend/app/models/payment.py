from app.extensions import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    mpesa_receipt_number = db.Column(db.String(50))
    phone_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed
    checkout_request_id = db.Column(db.String(100))
    merchant_request_id = db.Column(db.String(100))
    result_code = db.Column(db.Integer)
    result_desc = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    adventure_id = db.Column(db.Integer, db.ForeignKey('adventures.id'), nullable=False)
    
    # Relationship with booking (one-to-one)
    booking = db.relationship('Booking', backref='payment_rel', uselist=False)

    def to_dict(self):
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
            'adventure_id': self.adventure_id,
            'booking_id': self.booking.id if self.booking else None,
            'adventure_title': self.adventure.title if self.adventure else None,
            'user_username': self.user.username if self.user else None
        }