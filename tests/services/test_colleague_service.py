from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.colleague import Colleague
from app.db.repositories.booking_repository import BookingRepository
from app.db.repositories.colleague_repository import ColleagueRepository
from app.exceptions import ColleagueNotFoundError
from app.schemas.booking import BookingCreate, MeetingDurationMinutes, MeetingProvider, MeetingTimezone
from app.services.colleague_service import ColleagueService


@pytest.mark.asyncio
async def test_list_colleagues_respects_limit_and_offset(db_session: AsyncSession) -> None:
    db_session.add(
        Colleague(
            id=2,
            name="Alice Ops",
            default_meeting_provider=MeetingProvider.ZOOM,
            timezone=MeetingTimezone.UTC,
            meeting_duration_minutes=MeetingDurationMinutes.THIRTY,
        )
    )
    await db_session.commit()

    service = ColleagueService(ColleagueRepository(db_session), BookingRepository(db_session))

    page = await service.list_colleagues(limit=1, offset=1)

    assert len(page) == 1
    assert page[0].id == 2


@pytest.mark.asyncio
async def test_get_availability_raises_not_found_for_missing_colleague(db_session: AsyncSession) -> None:
    service = ColleagueService(ColleagueRepository(db_session), BookingRepository(db_session))

    with pytest.raises(ColleagueNotFoundError):
        await service.get_availability(999, datetime(2026, 1, 1, 0, 0), datetime(2026, 1, 2, 0, 0))


@pytest.mark.asyncio
async def test_get_availability_excludes_booked_slots(db_session: AsyncSession) -> None:
    booking_repo = BookingRepository(db_session)
    service = ColleagueService(ColleagueRepository(db_session), booking_repo)

    await booking_repo.create(
        BookingCreate(
            slot_start=datetime(2026, 1, 1, 10, 0),
            customer_name="Taken",
            customer_email="taken@example.com",
            colleague_id=1,
        )
    )

    result = await service.get_availability(1, datetime(2026, 1, 1, 0, 0), datetime(2026, 1, 2, 0, 0))

    assert all(slot.slot_start != datetime(2026, 1, 1, 10, 0) for slot in result.slots)
