from datetime import datetime

import pytest

from app.db.repositories.booking_repository import BookingRepository
from app.exceptions import BookingNotFoundError, SlotNotAvailableError
from app.schemas.booking import BookingCreate, BookingUpcomingQuery
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


@pytest.mark.asyncio
async def test_list_upcoming_returns_sorted_page() -> None:
    service = BookingService(BookingRepository())

    await service.create_booking(
        BookingCreate(
            slot_start=datetime(2026, 1, 1, 12, 0),
            customer_name="Late",
            customer_email="late@example.com",
        )
    )
    await service.create_booking(
        BookingCreate(
            slot_start=datetime(2026, 1, 1, 10, 0),
            customer_name="Early",
            customer_email="early@example.com",
        )
    )

    result = await service.list_upcoming(
        BookingUpcomingQuery(from_ts=datetime(2026, 1, 1, 9, 0), limit=1, offset=0)
    )

    assert len(result) == 1
    assert result[0].customer_name == "Early"
