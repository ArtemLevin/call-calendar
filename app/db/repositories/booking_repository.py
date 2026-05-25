from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.booking import Booking
from app.exceptions import SlotNotAvailableError
from app.schemas.booking import BookingCreate, BookingStatus


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
            meeting_provider=data.meeting_provider,
            meeting_timezone=data.meeting_timezone,
            meeting_duration_minutes=data.meeting_duration_minutes,
        )
        self.session.add(booking)
        # Why: slot conflicts are a write-time race condition, so we treat database
        # uniqueness as the source of truth and convert integrity violations into a
        # stable domain error the API layer already knows how to expose.
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            if self._is_slot_uniqueness_conflict(exc):
                raise SlotNotAvailableError(str(data.slot_start)) from exc
            raise
        await self.session.refresh(booking)
        return booking

    @staticmethod
    def _is_slot_uniqueness_conflict(exc: IntegrityError) -> bool:
        # Why: only slot uniqueness violations should be converted into a domain
        # availability error; other integrity failures must surface unchanged.
        error_text = str(exc.orig).lower() if exc.orig is not None else ""
        return "bookings.slot_start" in error_text and "unique" in error_text

    async def list_upcoming(
        self,
        from_ts: datetime,
        status: BookingStatus | None,
        limit: int,
        offset: int,
    ) -> list[Booking]:
        # Why: DB-side filtering/pagination avoids materializing full datasets in API
        # memory, which keeps latency and memory use stable as data grows.
        stmt: Select[tuple[Booking]] = select(Booking).where(Booking.slot_start >= from_ts)
        # Why: optional status filtering supports owner-oriented read views while
        # keeping the endpoint contract backward compatible when filter is omitted.
        if status is not None:
            stmt = stmt.where(Booking.status == status)
        stmt = stmt.order_by(Booking.slot_start.asc(), Booking.id.asc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, booking: Booking) -> Booking:
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
