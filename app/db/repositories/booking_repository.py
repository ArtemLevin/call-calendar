from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.booking import Booking
from app.schemas.booking import BookingCreate


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        # Why: requiring a live session makes transaction boundaries explicit,
        # which prevents hidden in-memory behavior from diverging across environments.
        self.session = session

    async def get_by_id(self, booking_id: int) -> Booking | None:
        stmt: Select[tuple[Booking]] = select(Booking).where(Booking.id == booking_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: BookingCreate) -> Booking:
        booking = Booking(
            slot_start=data.slot_start,
            customer_name=data.customer_name,
            customer_email=str(data.customer_email),
        )
        self.session.add(booking)
        # Why: persisting immediately surfaces integrity conflicts at the write point,
        # which keeps service-level error handling accurate under concurrent traffic.
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def is_slot_available(self, slot_start: datetime) -> bool:
        stmt: Select[tuple[int]] = select(Booking.id).where(Booking.slot_start == slot_start).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is None

    async def list_upcoming(self, from_ts: datetime, limit: int, offset: int) -> list[Booking]:
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
