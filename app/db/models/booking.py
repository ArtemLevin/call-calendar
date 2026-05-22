from dataclasses import dataclass
from datetime import datetime

from app.schemas.booking import BookingStatus


@dataclass
class Booking:
    """Domain booking entity used by current in-memory repository tests."""

    id: int
    slot_start: datetime
    customer_name: str
    customer_email: str
    status: BookingStatus = BookingStatus.PENDING
