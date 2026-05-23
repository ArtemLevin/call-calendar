from datetime import datetime

from sqlalchemy import Select, select
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

    async def list_upcoming(self, from_ts: datetime, limit: int, offset: int) -> list[Booking]:
        if self.session is None:
            # Why: sorting by time and id guarantees deterministic paging semantics,
            # which prevents clients from seeing duplicate or skipped records.
            upcoming = [item for item in self._items.values() if item.slot_start >= from_ts]
            upcoming.sort(key=lambda item: (item.slot_start, item.id))
            return upcoming[offset : offset + limit]

        # Why: DB-side filtering/pagination avoids materializing full datasets in API
        # memory, which keeps latency and memory use stable as data grows.
        stmt: Select[tuple[Booking]] = (
            select(Booking)
            .where(Booking.slot_start >= from_ts)
            .order_by(Booking.slot_start.asc(), Booking.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
