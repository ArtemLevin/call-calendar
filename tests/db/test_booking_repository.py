from datetime import datetime

import pytest

from app.db.repositories.booking_repository import BookingRepository
from app.schemas.booking import BookingCreate


@pytest.mark.asyncio
async def test_repository_create_and_get() -> None:
    repo = BookingRepository()
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
async def test_repository_slot_availability_changes_after_create() -> None:
    repo = BookingRepository()
    slot = datetime(2026, 1, 1, 9, 30)
    data = BookingCreate(
        slot_start=slot,
        customer_name="Repo User",
        customer_email="repo@example.com",
    )

    assert await repo.is_slot_available(str(slot))
    await repo.create(data)
    assert not await repo.is_slot_available(str(slot))
