from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.booking_repository import BookingRepository
from app.db.session import get_db_session
from app.exceptions import BookingNotFoundError, SlotNotAvailableError
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import BookingService

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
    except SlotNotAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return BookingResponse.model_validate(booking)


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
