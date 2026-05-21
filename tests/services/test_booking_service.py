from datetime import datetime

import pytest

from app.db.repositories.booking_repository import BookingRepository
from app.exceptions import BookingNotFoundError, SlotNotAvailableError
from app.schemas.booking import BookingCreate
from app.services.booking_service import BookingService


@pytest.mark.asyncio
async def test_create_booking_success() -> None:
    service = BookingService(BookingRepository())
    payload = BookingCreate(
        slot_start=datetime(2026, 1, 1, 10, 0),
        customer_name="Alice",
        customer_email="alice@example.com",
    )

    booking = await service.create_booking(payload)

    assert booking.id == 1
    assert booking.customer_name == "Alice"


@pytest.mark.asyncio
async def test_create_booking_conflict() -> None:
    service = BookingService(BookingRepository())
    payload = BookingCreate(
        slot_start=datetime(2026, 1, 1, 10, 0),
        customer_name="Alice",
        customer_email="alice@example.com",
    )

    await service.create_booking(payload)

    with pytest.raises(SlotNotAvailableError):
        await service.create_booking(payload)


@pytest.mark.asyncio
async def test_get_booking_not_found() -> None:
    service = BookingService(BookingRepository())

    with pytest.raises(BookingNotFoundError):
        await service.get_by_id(999)
