import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.meeting_settings_repository import MeetingSettingsRepository
from app.services.meeting_settings_service import MeetingSettingsService
from app.schemas.booking import MeetingDurationMinutes, MeetingProvider, MeetingTimezone


@pytest.mark.asyncio
async def test_get_meeting_settings_returns_default_when_empty(db_session: AsyncSession) -> None:
    service = MeetingSettingsService(MeetingSettingsRepository(db_session))

    provider, timezone, duration = await service.get_settings()

    assert provider == MeetingProvider.GOOGLE_MEET
    assert timezone == MeetingTimezone.ASIA_YEKATERINBURG
    assert duration == MeetingDurationMinutes.THIRTY


@pytest.mark.asyncio
async def test_update_meeting_settings_persists_and_returns_updated_values(
    db_session: AsyncSession,
) -> None:
    service = MeetingSettingsService(MeetingSettingsRepository(db_session))

    updated = await service.update_settings(
        meeting_provider=MeetingProvider.ZOOM,
        meeting_timezone=MeetingTimezone.UTC,
        meeting_duration_minutes=MeetingDurationMinutes.THIRTY,
    )
    fetched = await service.get_settings()

    assert updated == (
        MeetingProvider.ZOOM,
        MeetingTimezone.UTC,
        MeetingDurationMinutes.THIRTY,
    )
    assert fetched == updated
