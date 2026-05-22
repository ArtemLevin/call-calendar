"""SQLAlchemy-based repository for booking data access with transaction safety.

This repository uses async sessions and leverages DB-level constraints
to prevent race conditions during concurrent booking attempts.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.booking import Booking
from app.exceptions import SlotNotAvailableError
from app.schemas.booking import BookingCreate, BookingStatus


class BookingRepository:
    """Async SQLAlchemy repository for booking operations.
    
    Uses transactions and unique constraints to ensure data integrity
    and prevent double-booking under concurrent load.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, booking_id: int) -> Booking | None:
        """Fetch booking by ID."""
        result = await self._session.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: BookingCreate) -> Booking:
        """Create a new booking within the current transaction.
        
        Raises:
            SlotNotAvailableError: If slot is already booked (IntegrityError).
        """
        booking = Booking(
            slot_start=data.slot_start,
            customer_name=data.customer_name,
            customer_email=str(data.customer_email),
            status=BookingStatus.PENDING,
        )
        
        try:
            self._session.add(booking)
            await self._session.flush()  # Get ID without committing
            await self._session.refresh(booking)
            return booking
        except IntegrityError as exc:
            # Unique constraint violation: slot already booked
            await self._session.rollback()
            raise SlotNotAvailableError(str(data.slot_start)) from exc

    async def is_slot_available(self, slot_start: str) -> bool:
        """Check if a time slot is available for booking.
        
        Note: This method is prone to race conditions if used alone.
        The create() method handles this via DB-level unique constraint.
        """
        result = await self._session.execute(
            select(Booking).where(Booking.slot_start == slot_start)
        )
        existing = result.scalar_one_or_none()
        return existing is None
