from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.booking import Booking
from app.schemas.booking import BookingCreate


class BookingRepository:
    """Simple in-memory repository for bootstrap stage."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self.session = session
        self._items: dict[int, Booking] = {}
        self._next_id: int = 1

    async def get_by_id(self, booking_id: int) -> Booking | None:
        return self._items.get(booking_id)

    async def create(self, data: BookingCreate) -> Booking:
        booking = Booking(
            id=self._next_id,
            slot_start=data.slot_start,
            customer_name=data.customer_name,
            customer_email=str(data.customer_email),
        )
        self._items[self._next_id] = booking
        self._next_id += 1
        return booking

    async def is_slot_available(self, slot_start: str) -> bool:
        return all(str(item.slot_start) != str(slot_start) for item in self._items.values())
