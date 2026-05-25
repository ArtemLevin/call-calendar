import asyncio
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.db.repositories.booking_repository import BookingRepository
from app.exceptions import (
    BookingNotFoundError,
    InvalidBookingSlotError,
    InvalidBookingStatusTransitionError,
    SlotNotAvailableError,
)
from app.schemas.booking import BookingCreate, BookingStatus, BookingUpcomingQuery
from app.services.booking_service import BookingService


@pytest.mark.asyncio
async def test_create_booking_success(db_session: AsyncSession) -> None:
    service = BookingService(BookingRepository(db_session))
    payload = BookingCreate(
        slot_start=datetime(2026, 1, 1, 10, 0),
        customer_name="Alice",
        customer_email="alice@example.com",
    )

    booking = await service.create_booking(payload)

    assert booking.id >= 1
    assert booking.customer_name == "Alice"


@pytest.mark.asyncio
async def test_create_booking_conflict(db_session: AsyncSession) -> None:
    service = BookingService(BookingRepository(db_session))
    payload = BookingCreate(
        slot_start=datetime(2026, 1, 1, 10, 0),
        customer_name="Alice",
        customer_email="alice@example.com",
    )

    await service.create_booking(payload)

    with pytest.raises(SlotNotAvailableError):
        await service.create_booking(payload)


@pytest.mark.asyncio
async def test_create_booking_concurrent_conflict(test_engine: AsyncEngine) -> None:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False, autoflush=False)
    payload = BookingCreate(
        slot_start=datetime(2026, 1, 1, 10, 30),
        customer_name="Race",
        customer_email="race@example.com",
    )

    async def attempt_create() -> object:
        async with session_factory() as session:
            service = BookingService(BookingRepository(session))
            return await service.create_booking(payload)

    # Why: AsyncSession is not safe for concurrent use, so each racing request gets
    # an isolated session to mirror production request-scoped transaction boundaries.
    results = await asyncio.gather(attempt_create(), attempt_create(), return_exceptions=True)
    successes = [item for item in results if not isinstance(item, Exception)]
    conflicts = [item for item in results if isinstance(item, SlotNotAvailableError)]

    assert len(successes) == 1
    assert len(conflicts) == 1

    async with session_factory() as verification_session:
        verification_service = BookingService(BookingRepository(verification_session))
        persisted = await verification_service.list_upcoming(
            BookingUpcomingQuery(from_ts=datetime(2026, 1, 1, 10, 29), limit=10, offset=0)
        )
    assert len([booking for booking in persisted if booking.slot_start == payload.slot_start]) == 1


@pytest.mark.asyncio
async def test_get_booking_not_found(db_session: AsyncSession) -> None:
    service = BookingService(BookingRepository(db_session))

    with pytest.raises(BookingNotFoundError):
        await service.get_by_id(999)


@pytest.mark.asyncio
async def test_list_upcoming_returns_sorted_page(db_session: AsyncSession) -> None:
    service = BookingService(BookingRepository(db_session))

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


@pytest.mark.asyncio
async def test_create_booking_rejects_non_30_minute_slot(db_session: AsyncSession) -> None:
    service = BookingService(BookingRepository(db_session))

    with pytest.raises(InvalidBookingSlotError):
        await service.create_booking(
            BookingCreate(
                slot_start=datetime(2026, 1, 1, 10, 15),
                customer_name="Invalid",
                customer_email="invalid@example.com",
            )
        )


@pytest.mark.asyncio
async def test_create_booking_normalizes_timezone_aware_slot(db_session: AsyncSession) -> None:
    service = BookingService(BookingRepository(db_session))
    aware_plus_three = datetime.fromisoformat("2026-01-01T13:00:00+03:00")

    created = await service.create_booking(
        BookingCreate(
            slot_start=aware_plus_three,
            customer_name="Aware",
            customer_email="aware@example.com",
        )
    )

    assert created.slot_start == datetime(2026, 1, 1, 10, 0)


@pytest.mark.asyncio
async def test_list_upcoming_normalizes_timezone_aware_from_ts(db_session: AsyncSession) -> None:
    service = BookingService(BookingRepository(db_session))
    await service.create_booking(
        BookingCreate(
            slot_start=datetime(2026, 1, 1, 10, 0),
            customer_name="First",
            customer_email="first@example.com",
        )
    )

    result = await service.list_upcoming(
        BookingUpcomingQuery(
            from_ts=datetime.fromisoformat("2026-01-01T12:30:00+03:00"),
            limit=10,
            offset=0,
        )
    )

    assert len(result) == 1


@pytest.mark.asyncio
async def test_update_status_allows_pending_to_confirmed(db_session: AsyncSession) -> None:
    service = BookingService(BookingRepository(db_session))
    created = await service.create_booking(
        BookingCreate(
            slot_start=datetime(2026, 1, 1, 11, 0),
            customer_name="State",
            customer_email="state@example.com",
        )
    )

    updated = await service.update_status(created.id, BookingStatus.CONFIRMED)

    assert updated.status == BookingStatus.CONFIRMED


@pytest.mark.asyncio
async def test_update_status_rejects_completed_to_pending(db_session: AsyncSession) -> None:
    service = BookingService(BookingRepository(db_session))
    created = await service.create_booking(
        BookingCreate(
            slot_start=datetime(2026, 1, 1, 11, 30),
            customer_name="State",
            customer_email="state2@example.com",
        )
    )
    confirmed = await service.update_status(created.id, BookingStatus.CONFIRMED)
    completed = await service.update_status(confirmed.id, BookingStatus.COMPLETED)

    with pytest.raises(InvalidBookingStatusTransitionError):
        await service.update_status(completed.id, BookingStatus.PENDING)
