from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.meeting_settings import MeetingSettings
from app.schemas.booking import (
    MeetingDurationMinutes,
    MeetingProvider,
    MeetingTimezone,
)


class MeetingSettingsRepository:
    _SINGLETON_ID = 1

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self) -> MeetingSettings | None:
        stmt = select(MeetingSettings).where(MeetingSettings.id == self._SINGLETON_ID)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save(
        self,
        meeting_provider: MeetingProvider,
        meeting_timezone: MeetingTimezone,
        meeting_duration_minutes: MeetingDurationMinutes,
    ) -> MeetingSettings:
        entity = await self.get()
        if entity is None:
            entity = MeetingSettings(
                id=self._SINGLETON_ID,
                meeting_provider=meeting_provider,
                meeting_timezone=meeting_timezone,
                meeting_duration_minutes=meeting_duration_minutes,
            )
        else:
            entity.meeting_provider = meeting_provider
            entity.meeting_timezone = meeting_timezone
            entity.meeting_duration_minutes = meeting_duration_minutes

        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
