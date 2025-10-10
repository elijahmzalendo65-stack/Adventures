from app.extensions import db

class Adventure(db.Model):
    __tablename__ = 'adventures'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.String(100))
    difficulty = db.Column(db.String(50))
    image_url = db.Column(db.String(500))
    max_capacity = db.Column(db.Integer, default=10)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    payments = db.relationship('Payment', backref='adventure', lazy=True)
    bookings = db.relationship('Booking', backref='adventure', lazy=True)

    def to_dict(self):
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
            'creator_username': self.creator.username if self.creator else None
        }