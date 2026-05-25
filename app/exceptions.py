class BookingError(Exception):
    """Base exception for booking domain errors."""


class BookingNotFoundError(BookingError):
    """Raised when booking is not found."""

    def __init__(self, booking_id: int):
        super().__init__(f"Booking with id={booking_id} not found")
        self.booking_id = booking_id


class SlotNotAvailableError(BookingError):
    """Raised when slot is already booked."""

    def __init__(self, slot_start: str):
        super().__init__(f"Slot {slot_start} is not available")
        self.slot_start = slot_start


class InvalidBookingSlotError(BookingError):
    """Raised when slot violates booking policy constraints."""

    def __init__(self, slot_start: str):
        super().__init__(
            f"Slot {slot_start} must be aligned to 30-minute boundaries with zero seconds"
        )
        self.slot_start = slot_start
