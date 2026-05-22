from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.schemas.booking import BookingStatus


class Booking(Base):
    """SQLAlchemy ORM model for booking records.
    
    Table schema:
    - id: Primary key (auto-increment)
    - slot_start: Unique datetime to prevent double-booking
    - customer_name: Customer's full name
    - customer_email: Customer's email address
    - status: Booking status (PENDING, CONFIRMED, etc.)
    
    Unique constraint on slot_start prevents race conditions at DB level.
    """

    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("slot_start", name="uq_bookings_slot_start"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slot_start: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(default=BookingStatus.PENDING, nullable=False)
