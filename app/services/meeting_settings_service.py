from app.db.repositories.meeting_settings_repository import MeetingSettingsRepository
from app.schemas.booking import (
    MeetingDurationMinutes,
    MeetingProvider,
    MeetingTimezone,
)


class MeetingSettingsService:
    def __init__(self, repository: MeetingSettingsRepository) -> None:
        self.repository = repository

    async def get_settings(self) -> tuple[MeetingProvider, MeetingTimezone, MeetingDurationMinutes]:
        stored = await self.repository.get()
        if stored is None:
            return (
                MeetingProvider.GOOGLE_MEET,
                MeetingTimezone.ASIA_YEKATERINBURG,
                MeetingDurationMinutes.THIRTY,
            )
        return (stored.meeting_provider, stored.meeting_timezone, stored.meeting_duration_minutes)

    async def update_settings(
        self,
        meeting_provider: MeetingProvider,
        meeting_timezone: MeetingTimezone,
        meeting_duration_minutes: MeetingDurationMinutes,
    ) -> tuple[MeetingProvider, MeetingTimezone, MeetingDurationMinutes]:
        # Why: persistence at service boundary guarantees GET reflects latest PATCH
        # values and avoids split-brain defaults across API replicas.
        stored = await self.repository.save(
            meeting_provider=meeting_provider,
            meeting_timezone=meeting_timezone,
            meeting_duration_minutes=meeting_duration_minutes,
        )
        return (stored.meeting_provider, stored.meeting_timezone, stored.meeting_duration_minutes)
