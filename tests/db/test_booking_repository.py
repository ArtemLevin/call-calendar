from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.booking_repository import BookingRepository
from app.exceptions import SlotNotAvailableError
from app.schemas.booking import BookingCreate


@pytest.mark.asyncio
async def test_repository_create_and_get(db_session: AsyncSession) -> None:
    repo = BookingRepository(db_session)
    data = BookingCreate(
        slot_start=datetime(2026, 1, 1, 9, 0),
        customer_name="Repo User",
        customer_email="repo@example.com",
    )

    created = await repo.create(data)
    fetched = await repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_repository_create_raises_domain_conflict_on_duplicate_slot(
    db_session: AsyncSession,
) -> None:
    repo = BookingRepository(db_session)
    data = BookingCreate(
        slot_start=datetime(2026, 1, 1, 9, 30),
        customer_name="Repo User",
        customer_email="repo@example.com",
    )

    await repo.create(data)

    with pytest.raises(SlotNotAvailableError):
        await repo.create(data)


@pytest.mark.asyncio
async def test_repository_recovers_session_after_conflict(db_session: AsyncSession) -> None:
    repo = BookingRepository(db_session)
    conflict_slot = datetime(2026, 1, 1, 9, 45)
    await repo.create(
        BookingCreate(
            slot_start=conflict_slot,
            customer_name="Taken",
            customer_email="taken@example.com",
        )
    )

    with pytest.raises(SlotNotAvailableError):
        await repo.create(
            BookingCreate(
                slot_start=conflict_slot,
                customer_name="Duplicate",
                customer_email="dup@example.com",
            )
        )

    created = await repo.create(
        BookingCreate(
            slot_start=datetime(2026, 1, 1, 10, 15),
            customer_name="Fresh",
            customer_email="fresh@example.com",
        )
    )

    assert created.id >= 1


@pytest.mark.asyncio
async def test_repository_list_upcoming_applies_filter_sort_and_pagination(db_session: AsyncSession) -> None:
    repo = BookingRepository(db_session)
    await repo.create(
        BookingCreate(
            slot_start=datetime(2026, 1, 1, 12, 0),
            customer_name="Later",
            customer_email="later@example.com",
        )
    )
    await repo.create(
        BookingCreate(
            slot_start=datetime(2026, 1, 1, 10, 0),
            customer_name="First",
            customer_email="first@example.com",
        )
    )
    await repo.create(
        BookingCreate(
            slot_start=datetime(2026, 1, 1, 11, 0),
            customer_name="Middle",
            customer_email="middle@example.com",
        )
    )

    page = await repo.list_upcoming(from_ts=datetime(2026, 1, 1, 10, 30), limit=1, offset=0)

    assert len(page) == 1
    assert page[0].customer_name == "Middle"
