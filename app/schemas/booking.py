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


class BookingResponse(BaseModel):
    id: int
    slot_start: datetime
    customer_name: str
    customer_email: EmailStr
    status: BookingStatus

    model_config = {"from_attributes": True}
