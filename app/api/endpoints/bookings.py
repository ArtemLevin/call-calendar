from collections.abc import Generator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.booking_repository import BookingRepository
from app.db.session import get_db_session
from app.exceptions import BookingNotFoundError, InvalidBookingSlotError, SlotNotAvailableError
from app.schemas.booking import BookingCreate, BookingResponse, BookingUpcomingQuery
from app.services.booking_service import BookingService, get_utc_now_naive

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def get_booking_repository(db: AsyncSession = Depends(get_db_session)) -> BookingRepository:
    return BookingRepository(session=db)


def get_booking_service(
    repository: BookingRepository = Depends(get_booking_repository),
) -> BookingService:
    return BookingService(repository)


def get_booking_service_dep(
    service: BookingService = Depends(get_booking_service),
) -> Generator[BookingService, None, None]:
    yield service


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    service: BookingService = Depends(get_booking_service_dep),
) -> BookingResponse:
    try:
        booking = await service.create_booking(data)
    except InvalidBookingSlotError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except SlotNotAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return BookingResponse.model_validate(booking)


@router.get("/upcoming", response_model=list[BookingResponse])
async def list_upcoming_bookings(
    from_ts: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: BookingService = Depends(get_booking_service_dep),
) -> list[BookingResponse]:
    # Why: centralizing default time selection at the endpoint boundary guarantees
    # clients get stable behavior even when they omit optional query parameters.
    query = BookingUpcomingQuery(
        from_ts=from_ts if from_ts is not None else get_utc_now_naive(),
        limit=limit,
        offset=offset,
    )
    bookings = await service.list_upcoming(query)
    return [BookingResponse.model_validate(booking) for booking in bookings]


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    service: BookingService = Depends(get_booking_service_dep),
) -> BookingResponse:
    try:
        booking = await service.get_by_id(booking_id)
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BookingResponse.model_validate(booking)

