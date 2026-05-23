from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BookingCreate(BaseModel):
    slot_start: datetime
    customer_name: str = Field(min_length=2, max_length=255)
    customer_email: EmailStr


class BookingUpcomingQuery(BaseModel):
    from_ts: datetime
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class BookingResponse(BaseModel):
    id: int
    slot_start: datetime
    customer_name: str
    customer_email: EmailStr
    status: BookingStatus

    model_config = {"from_attributes": True}
