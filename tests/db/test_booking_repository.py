from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.booking_repository import BookingRepository
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
async def test_repository_slot_availability_changes_after_create(db_session: AsyncSession) -> None:
    repo = BookingRepository(db_session)
    slot = datetime(2026, 1, 1, 9, 30)
    data = BookingCreate(
        slot_start=slot,
        customer_name="Repo User",
        customer_email="repo@example.com",
    )

    assert await repo.is_slot_available(slot)
    await repo.create(data)
    assert not await repo.is_slot_available(slot)


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
