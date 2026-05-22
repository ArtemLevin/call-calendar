from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.booking import Booking
from app.db.repositories.booking_repository import BookingRepository
from app.exceptions import BookingNotFoundError, SlotNotAvailableError
from app.schemas.booking import BookingCreate


class BookingService:
    """Business logic for booking operations.
    
    Handles transaction management and coordinates repository operations.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.repository = BookingRepository(session)

    async def create_booking(self, data: BookingCreate) -> Booking:
        """Create a new booking with transaction safety.
        
        The repository handles IntegrityError from unique constraint violations.
        """
        is_available = await self.repository.is_slot_available(str(data.slot_start))
        if not is_available:
            raise SlotNotAvailableError(str(data.slot_start))
        
        booking = await self.repository.create(data)
        await self._session.commit()
        await self._session.refresh(booking)
        return booking

    async def get_by_id(self, booking_id: int) -> Booking:
        """Fetch booking by ID."""
        booking = await self.repository.get_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundError(booking_id)
        return booking
