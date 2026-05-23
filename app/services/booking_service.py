from datetime import datetime, timezone

from app.db.models.booking import Booking
from app.db.repositories.booking_repository import BookingRepository
from app.exceptions import BookingNotFoundError, SlotNotAvailableError
from app.schemas.booking import BookingCreate, BookingUpcomingQuery


class BookingService:
    def __init__(self, repository: BookingRepository) -> None:
        self.repository = repository

    async def create_booking(self, data: BookingCreate) -> Booking:
        is_available = await self.repository.is_slot_available(str(data.slot_start))
        if not is_available:
            raise SlotNotAvailableError(str(data.slot_start))
        return await self.repository.create(data)

    async def get_by_id(self, booking_id: int) -> Booking:
        booking = await self.repository.get_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundError(booking_id)
        return booking

    async def list_upcoming(self, query: BookingUpcomingQuery) -> list[Booking]:
        return await self.repository.list_upcoming(
            from_ts=query.from_ts,
            limit=query.limit,
            offset=query.offset,
        )


def get_utc_now_naive() -> datetime:
    # Why: runtime currently stores naive datetimes in persistence, so normalizing
    # now() to naive UTC avoids mixed-aware comparisons that would raise TypeError.
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)
