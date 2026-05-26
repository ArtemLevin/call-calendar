from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.booking import MeetingDurationMinutes, MeetingProvider, MeetingTimezone


class ColleagueContactOption(str, Enum):
    GOOGLE_MEET = MeetingProvider.GOOGLE_MEET.value
    ZOOM = MeetingProvider.ZOOM.value
    PHONE = MeetingProvider.PHONE.value


class ColleagueResponse(BaseModel):
    id: int
    name: str = Field(min_length=2, max_length=255)
    contact_options: list[ColleagueContactOption]
    default_meeting_provider: MeetingProvider
    timezone: MeetingTimezone
    meeting_duration_minutes: MeetingDurationMinutes

    model_config = {"from_attributes": True}


class ColleagueAvailabilityQuery(BaseModel):
    from_ts: datetime
    to_ts: datetime


class ColleagueAvailabilitySlot(BaseModel):
    slot_start: datetime
    meeting_provider_options: list[ColleagueContactOption]


class ColleagueAvailabilityResponse(BaseModel):
    colleague_id: int
    slots: list[ColleagueAvailabilitySlot]
