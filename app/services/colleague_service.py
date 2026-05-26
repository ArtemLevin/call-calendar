from datetime import datetime, timedelta

from app.db.repositories.booking_repository import BookingRepository
from app.db.repositories.colleague_repository import ColleagueRepository
from app.exceptions import ColleagueNotFoundError
from app.schemas.colleague import (
    ColleagueAvailabilityResponse,
    ColleagueAvailabilitySlot,
    ColleagueContactOption,
    ColleagueResponse,
)


class ColleagueService:
    WORKDAY_START_HOUR = 9
    WORKDAY_END_HOUR = 18

    def __init__(self, repository: ColleagueRepository, booking_repository: BookingRepository) -> None:
        self.repository = repository
        self.booking_repository = booking_repository

    async def list_colleagues(self) -> list[ColleagueResponse]:
        rows = await self.repository.list_all()
        return [
            ColleagueResponse(
                id=row.id,
                name=row.name,
                contact_options=[
                    ColleagueContactOption.GOOGLE_MEET,
                    ColleagueContactOption.ZOOM,
                    ColleagueContactOption.PHONE,
                ],
                default_meeting_provider=row.default_meeting_provider,
                timezone=row.timezone,
                meeting_duration_minutes=row.meeting_duration_minutes,
            )
            for row in rows
        ]

    async def get_availability(self, colleague_id: int, from_ts: datetime, to_ts: datetime) -> ColleagueAvailabilityResponse:
        colleague = await self.repository.get_by_id(colleague_id)
        if colleague is None:
            raise ColleagueNotFoundError(colleague_id)

        booked = await self.booking_repository.list_upcoming(
            from_ts=from_ts,
            to_ts=to_ts,
            status=None,
            limit=1000,
            offset=0,
            colleague_id=colleague_id,
        )
        booked_slots = {item.slot_start for item in booked}
        slots: list[ColleagueAvailabilitySlot] = []

        current_day = datetime(from_ts.year, from_ts.month, from_ts.day)
        end_day = datetime(to_ts.year, to_ts.month, to_ts.day)
        while current_day <= end_day:
            if current_day.weekday() < 5:
                for hour in range(self.WORKDAY_START_HOUR, self.WORKDAY_END_HOUR):
                    for minute in (0, 30):
                        slot = current_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        if from_ts <= slot < to_ts and slot not in booked_slots:
                            slots.append(
                                ColleagueAvailabilitySlot(
                                    slot_start=slot,
                                    meeting_provider_options=[
                                        ColleagueContactOption.GOOGLE_MEET,
                                        ColleagueContactOption.ZOOM,
                                        ColleagueContactOption.PHONE,
                                    ],
                                )
                            )
            current_day += timedelta(days=1)

        return ColleagueAvailabilityResponse(colleague_id=colleague_id, slots=slots)
