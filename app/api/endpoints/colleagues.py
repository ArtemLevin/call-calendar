from collections.abc import Generator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.booking_repository import BookingRepository
from app.db.repositories.colleague_repository import ColleagueRepository
from app.db.session import get_db_session
from app.exceptions import ColleagueNotFoundError
from app.schemas.colleague import ColleagueAvailabilityResponse, ColleagueResponse
from app.services.colleague_service import ColleagueService

router = APIRouter(prefix="/api/colleagues", tags=["colleagues"])


def get_colleague_repository(db: AsyncSession = Depends(get_db_session)) -> ColleagueRepository:
    return ColleagueRepository(session=db)


def get_booking_repository(db: AsyncSession = Depends(get_db_session)) -> BookingRepository:
    return BookingRepository(session=db)


def get_colleague_service(
    colleague_repository: ColleagueRepository = Depends(get_colleague_repository),
    booking_repository: BookingRepository = Depends(get_booking_repository),
) -> ColleagueService:
    return ColleagueService(colleague_repository, booking_repository)


def get_colleague_service_dep(
    service: ColleagueService = Depends(get_colleague_service),
) -> Generator[ColleagueService, None, None]:
    yield service


@router.get("/", response_model=list[ColleagueResponse])
async def list_colleagues(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: ColleagueService = Depends(get_colleague_service_dep),
) -> list[ColleagueResponse]:
    return await service.list_colleagues(limit=limit, offset=offset)


@router.get("/{colleague_id}/availability", response_model=ColleagueAvailabilityResponse)
async def get_colleague_availability(
    colleague_id: int,
    from_ts: datetime = Query(...),
    to_ts: datetime = Query(...),
    service: ColleagueService = Depends(get_colleague_service_dep),
) -> ColleagueAvailabilityResponse:
    if to_ts <= from_ts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="to_ts must be greater than from_ts",
        )
    try:
        return await service.get_availability(colleague_id=colleague_id, from_ts=from_ts, to_ts=to_ts)
    except ColleagueNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colleague not found") from exc
