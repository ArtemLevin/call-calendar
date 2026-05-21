from app.db.models.booking import Booking
from app.db.repositories.booking_repository import BookingRepository
from app.exceptions import BookingNotFoundError, SlotNotAvailableError
from app.schemas.booking import BookingCreate


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
