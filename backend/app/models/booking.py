# app/models/booking.py

from ..extensions import db
from datetime import datetime
import secrets
import string


class Booking(db.Model):
    __tablename__ = "bookings"

    # -----------------------------
    # Primary Key
    # -----------------------------
    id = db.Column(db.Integer, primary_key=True)

    # -----------------------------
    # Foreign Keys
    # -----------------------------
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    adventure_id = db.Column(
        db.Integer,
        db.ForeignKey("adventures.id", ondelete="CASCADE"),
        nullable=False
    )

    payment_id = db.Column(
        db.Integer,
        db.ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True
    )

    # -----------------------------
    # Booking Details
    # -----------------------------
    booking_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    adventure_date = db.Column(
        db.DateTime,
        nullable=False
    )

    number_of_people = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    total_amount = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    special_requests = db.Column(
        db.Text,
        nullable=True,
        default=""
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="pending"
    )  # pending, confirmed, cancelled, completed

    booking_reference = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # -----------------------------
    # Customer Details
    # (defaults added to avoid migration crashes)
    # -----------------------------
    customer_name = db.Column(
        db.String(100),
        nullable=False,
        default=""
    )

    customer_email = db.Column(
        db.String(150),
        nullable=False,
        default=""
    )

    customer_phone = db.Column(
        db.String(20),
        nullable=False,
        default=""
    )

    # -----------------------------
    # Timestamps
    # -----------------------------
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # -----------------------------
    # Relationships
    # -----------------------------
    user = db.relationship(
        "User",
        back_populates="bookings",
        lazy="joined"
    )

    adventure = db.relationship(
        "Adventure",
        back_populates="bookings",
        lazy="joined"
    )

    payment = db.relationship(
        "Payment",
        back_populates="booking",
        uselist=False,
        lazy="joined"
    )

    # -----------------------------
    # Initialization
    # -----------------------------
    def __init__(self, **kwargs):
        if not kwargs.get("booking_reference"):
            kwargs["booking_reference"] = self.generate_booking_reference()

        super().__init__(**kwargs)

    # -----------------------------
    # Utility Methods
    # -----------------------------
    @staticmethod
    def generate_booking_reference() -> str:
        """
        Generate a unique booking reference.
        Example: BK-A9X3FQ2P
        """
        chars = string.ascii_uppercase + string.digits
        return "BK-" + "".join(secrets.choice(chars) for _ in range(8))

    def calculate_total_amount(self) -> float:
        """
        Calculate total amount based on adventure price and number of people.
        """
        if self.adventure and self.number_of_people:
            self.total_amount = (self.adventure.price or 0) * self.number_of_people
        return self.total_amount

    # -----------------------------
    # Serialization
    # -----------------------------
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "adventure_id": self.adventure_id,
            "payment_id": self.payment_id,
            "booking_date": self.booking_date.isoformat(),
            "adventure_date": self.adventure_date.isoformat(),
            "number_of_people": self.number_of_people,
            "total_amount": self.total_amount,
            "special_requests": self.special_requests,
            "status": self.status,
            "booking_reference": self.booking_reference,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "user": self.user.to_dict() if self.user else None,
            "adventure": self.adventure.to_dict() if self.adventure else None,
            "payment": self.payment.to_dict() if self.payment else None,
        }
