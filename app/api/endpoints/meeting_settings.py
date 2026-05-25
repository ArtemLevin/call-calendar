from collections.abc import Generator

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.meeting_settings_repository import MeetingSettingsRepository
from app.db.session import get_db_session
from app.schemas.booking import (
    MeetingDurationMinutes,
    MeetingMetadataOptionsResponse,
    MeetingProvider,
    MeetingSettingsResponse,
    MeetingSettingsUpdate,
    MeetingTimezone,
)
from app.services.meeting_settings_service import MeetingSettingsService

router = APIRouter(tags=["meeting-settings"])


def get_meeting_settings_repository(
    db: AsyncSession = Depends(get_db_session),
) -> MeetingSettingsRepository:
    return MeetingSettingsRepository(session=db)


def get_meeting_settings_service(
    repository: MeetingSettingsRepository = Depends(get_meeting_settings_repository),
) -> MeetingSettingsService:
    return MeetingSettingsService(repository=repository)


def get_meeting_settings_service_dep(
    service: MeetingSettingsService = Depends(get_meeting_settings_service),
) -> Generator[MeetingSettingsService, None, None]:
    yield service


@router.get("/api/meeting-metadata/options", response_model=MeetingMetadataOptionsResponse)
async def get_meeting_metadata_options() -> MeetingMetadataOptionsResponse:
    return MeetingMetadataOptionsResponse(
        meeting_provider_options=list(MeetingProvider),
        meeting_timezone_options=list(MeetingTimezone),
        meeting_duration_minutes_options=list(MeetingDurationMinutes),
    )


@router.get("/api/meeting-settings", response_model=MeetingSettingsResponse)
async def get_meeting_settings(
    service: MeetingSettingsService = Depends(get_meeting_settings_service_dep),
) -> MeetingSettingsResponse:
    meeting_provider, meeting_timezone, meeting_duration_minutes = await service.get_settings()
    return MeetingSettingsResponse(
        meeting_provider=meeting_provider,
        meeting_timezone=meeting_timezone,
        meeting_duration_minutes=meeting_duration_minutes,
    )


@router.patch("/api/meeting-settings", response_model=MeetingSettingsResponse)
async def patch_meeting_settings(
    data: MeetingSettingsUpdate,
    service: MeetingSettingsService = Depends(get_meeting_settings_service_dep),
) -> MeetingSettingsResponse:
    meeting_provider, meeting_timezone, meeting_duration_minutes = await service.update_settings(
        meeting_provider=data.meeting_provider,
        meeting_timezone=data.meeting_timezone,
        meeting_duration_minutes=data.meeting_duration_minutes,
    )
    return MeetingSettingsResponse(
        meeting_provider=meeting_provider,
        meeting_timezone=meeting_timezone,
        meeting_duration_minutes=meeting_duration_minutes,
    )
