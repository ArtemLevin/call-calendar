from datetime import datetime, timezone

from app.db.models.booking import Booking
from app.db.repositories.booking_repository import BookingRepository
from app.db.repositories.meeting_settings_repository import MeetingSettingsRepository
from app.exceptions import (
    BookingNotFoundError,
    InvalidBookingSlotError,
    InvalidBookingStatusTransitionError,
)
from app.schemas.booking import BookingCreate, BookingStatus, BookingUpcomingQuery


class BookingService:
    _ALLOWED_STATUS_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
        BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
        BookingStatus.CONFIRMED: {BookingStatus.COMPLETED, BookingStatus.CANCELLED},
        BookingStatus.CANCELLED: set(),
        BookingStatus.COMPLETED: set(),
    }

    def __init__(
        self,
        repository: BookingRepository,
        meeting_settings_repository: MeetingSettingsRepository,
    ) -> None:
        self.repository = repository
        self.meeting_settings_repository = meeting_settings_repository

    async def create_booking(self, data: BookingCreate) -> Booking:
        normalized_slot_start = self._normalize_to_utc_naive(data.slot_start)
        self._ensure_slot_policy(normalized_slot_start)
        settings = await self.meeting_settings_repository.get()
        meeting_provider = (
            data.meeting_provider
            if data.meeting_provider is not None
            else settings.meeting_provider if settings is not None else Booking.DEFAULT_PROVIDER
        )
        meeting_timezone = (
            data.meeting_timezone
            if data.meeting_timezone is not None
            else settings.meeting_timezone if settings is not None else Booking.DEFAULT_TIMEZONE
        )
        meeting_duration = (
            data.meeting_duration_minutes
            if data.meeting_duration_minutes is not None
            else settings.meeting_duration_minutes if settings is not None else Booking.DEFAULT_DURATION
        )
        normalized_data = data.model_copy(
            update={
                "slot_start": normalized_slot_start,
                "meeting_provider": meeting_provider,
                "meeting_timezone": meeting_timezone,
                "meeting_duration_minutes": meeting_duration,
            }
        )
        return await self.repository.create(normalized_data)

    async def get_by_id(self, booking_id: int) -> Booking:
        booking = await self.repository.get_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundError(booking_id)
        return booking

    async def list_upcoming(self, query: BookingUpcomingQuery) -> list[Booking]:
        normalized_query = query.model_copy(
            update={"from_ts": self._normalize_to_utc_naive(query.from_ts)}
        )
        return await self.repository.list_upcoming(
            from_ts=normalized_query.from_ts,
            status=normalized_query.status,
            limit=normalized_query.limit,
            offset=normalized_query.offset,
        )

    async def update_status(self, booking_id: int, new_status: BookingStatus) -> Booking:
        booking = await self.get_by_id(booking_id)
        if new_status == booking.status:
            return booking

        allowed_transitions = self._ALLOWED_STATUS_TRANSITIONS[booking.status]
        if new_status not in allowed_transitions:
            raise InvalidBookingStatusTransitionError(
                current_status=booking.status.value,
                requested_status=new_status.value,
            )

        booking.status = new_status
        return await self.repository.save(booking)

    @staticmethod
    def _normalize_to_utc_naive(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _ensure_slot_policy(slot_start: datetime) -> None:
        if slot_start.second != 0 or slot_start.microsecond != 0:
            raise InvalidBookingSlotError(str(slot_start))
        if slot_start.minute not in {0, 30}:
            raise InvalidBookingSlotError(str(slot_start))


def get_utc_now_naive() -> datetime:
    # Why: runtime currently stores naive datetimes in persistence, so normalizing
    # now() to naive UTC avoids mixed-aware comparisons that would raise TypeError.
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)
