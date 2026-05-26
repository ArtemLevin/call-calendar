from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class MeetingProvider(str, Enum):
    GOOGLE_MEET = "google_meet"
    ZOOM = "zoom"
    PHONE = "phone"


class MeetingTimezone(str, Enum):
    ASIA_YEKATERINBURG = "Asia/Yekaterinburg"
    UTC = "UTC"
    EUROPE_BERLIN = "Europe/Berlin"
    AMERICA_NEW_YORK = "America/New_York"


class MeetingDurationMinutes(int, Enum):
    THIRTY = 30


class BookingCreate(BaseModel):
    slot_start: datetime
    customer_name: str = Field(min_length=2, max_length=255)
    customer_email: EmailStr
    meeting_provider: MeetingProvider | None = None
    meeting_timezone: MeetingTimezone | None = None
    meeting_duration_minutes: MeetingDurationMinutes | None = None
    colleague_id: int | None = Field(default=None, ge=1)


class BookingUpcomingQuery(BaseModel):
    from_ts: datetime
    status: BookingStatus | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


class BookingResponse(BaseModel):
    id: int
    slot_start: datetime
    customer_name: str
    customer_email: EmailStr
    status: BookingStatus
    meeting_provider: MeetingProvider
    meeting_timezone: MeetingTimezone
    meeting_duration_minutes: MeetingDurationMinutes

    model_config = {"from_attributes": True}


class MeetingSettingsResponse(BaseModel):
    meeting_provider: MeetingProvider
    meeting_timezone: MeetingTimezone
    meeting_duration_minutes: MeetingDurationMinutes


class MeetingSettingsUpdate(BaseModel):
    meeting_provider: MeetingProvider
    meeting_timezone: MeetingTimezone
    meeting_duration_minutes: MeetingDurationMinutes


class MeetingMetadataOptionsResponse(BaseModel):
    meeting_provider_options: list[MeetingProvider]
    meeting_timezone_options: list[MeetingTimezone]
    meeting_duration_minutes_options: list[MeetingDurationMinutes]
