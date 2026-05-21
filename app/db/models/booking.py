from dataclasses import dataclass
from datetime import datetime

from app.schemas.booking import BookingStatus


@dataclass
class Booking:
    id: int
    slot_start: datetime
    customer_name: str
    customer_email: str
    status: BookingStatus = BookingStatus.PENDING
