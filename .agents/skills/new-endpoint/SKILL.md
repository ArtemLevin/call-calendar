---
name: new-endpoint
description: Create new API endpoints following project architecture patterns. Use when adding new routes or extending existing ones.
---

# New Endpoint Skill

## Assumptions / Verify first

Before following examples below, verify the expected project paths exist in the current repository:

```bash
rg --files | head -n 50
for p in app tests alembic; do
  if [ -d "$p" ]; then
    echo "OK: $p/"
  else
    echo "MISSING: $p/ (examples below may be pseudocode)"
  fi
done
```

If those directories are missing, treat path-based examples as **pseudocode** and adapt commands to real repo paths.

## Purpose

Add new API endpoints that follow the layered architecture: Endpoint → Service → Repository → Database.

## Workflow

### Phase 1: Explore

1. Read existing endpoints in `/app/api/endpoints/`.
2. Understand the domain model involved.
3. Check if service layer exists for this domain.
4. Review Pydantic schemas in `/app/schemas/`.

### Phase 2: Plan

Write an implementation plan:

```markdown
## Plan: Add GET /api/bookings/{id} endpoint

### Components to Create/Modify

1. Schema: BookingResponse (may exist)
2. Service: BookingService.get_by_id() (new method)
3. Repository: BookingRepository.get_by_id() (new method)
4. Endpoint: bookings.py (new route)

### Dependencies

- Import BookingService in endpoint
- Import BookingResponse schema
- Handle 404 error case

### Testing Strategy

- Unit test for service method
- Integration test for endpoint
- Test 404 case
```

### Phase 3: Code

#### Step 1: Define Pydantic Schema

```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /app/schemas/booking.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class BookingResponse(BaseModel):
    """Response schema for booking data."""
    id: int
    slot_start: datetime
    customer_name: str
    customer_email: EmailStr
    status: BookingStatus
    created_at: datetime
    
    class Config:
        from_attributes = True  # Allows ORM mode
```

#### Step 2: Add Repository Method

```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /app/db/repositories/booking_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.booking import Booking
from typing import Optional

class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, booking_id: int) -> Optional[Booking]:
        """Get booking by ID. Returns None if not found."""
        result = await self.session.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()
```

#### Step 3: Add Service Method

```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /app/services/booking_service.py
from app.db.repositories.booking_repository import BookingRepository
from app.db.models.booking import Booking
from app.exceptions import BookingNotFoundError
from typing import Optional

class BookingService:
    def __init__(self, repository: BookingRepository):
        self.repository = repository
    
    async def get_by_id(self, booking_id: int) -> Booking:
        """
        Get booking by ID.
        
        Raises:
            BookingNotFoundError: If booking doesn't exist.
        """
        booking = await self.repository.get_by_id(booking_id)
        
        if booking is None:
            raise BookingNotFoundError(booking_id)
        
        return booking
```

#### Step 4: Create Endpoint

```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /app/api/endpoints/bookings.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.services.booking_service import BookingService
from app.schemas.booking import BookingResponse
from app.exceptions import BookingNotFoundError

router = APIRouter(prefix="/api/bookings", tags=["bookings"])

def get_booking_service(db: AsyncSession = Depends(get_db_session)) -> BookingService:
    """Dependency injector for BookingService."""
    from app.db.repositories.booking_repository import BookingRepository
    repo = BookingRepository(db)
    return BookingService(repo)

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    service: BookingService = Depends(get_booking_service)
) -> BookingResponse:
    """
    Get a specific booking by ID.
    
    - **booking_id**: Unique identifier of the booking
    - Returns: Booking details including status
    - Raises: 404 if booking not found
    """
    try:
        booking = await service.get_by_id(booking_id)
        return BookingResponse.model_validate(booking)
    except BookingNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
```

#### Step 5: Add Exception Class

```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /app/exceptions.py
class BookingNotFoundError(Exception):
    """Raised when a booking is not found."""
    
    def __init__(self, booking_id: int):
        self.booking_id = booking_id
        super().__init__(f"Booking with ID {booking_id} not found")
```

### Phase 4: Verify

1. Run `make lint` — ensure code style compliance.
2. Run `make typecheck` — verify type annotations.
3. Write and run tests.
4. Test endpoint manually with curl or browser.

```bash
# Test endpoint
curl http://localhost:8000/api/bookings/1

# Should return 404 for non-existent
curl http://localhost:8000/api/bookings/999
```

## What NOT to Do

- ❌ Do NOT put business logic in endpoints.
- ❌ Do NOT access database directly from endpoints.
- ❌ Do NOT return ORM models directly (use Pydantic).
- ❌ Do NOT skip error handling.
- ❌ Do NOT forget response_model annotation.

## Endpoint Patterns

### Standard CRUD Pattern

```python
@router.get("/", response_model=list[BookingResponse])
async def list_bookings(...) -> list[BookingResponse]:
    ...

@router.get("/{id}", response_model=BookingResponse)
async def get_booking(id: int, ...) -> BookingResponse:
    ...

@router.post("/", response_model=BookingResponse, status_code=201)
async def create_booking(data: BookingCreate, ...) -> BookingResponse:
    ...

@router.put("/{id}", response_model=BookingResponse)
async def update_booking(id: int, data: BookingUpdate, ...) -> BookingResponse:
    ...

@router.delete("/{id}", status_code=204)
async def delete_booking(id: int, ...) -> None:
    ...
```

### Error Handling Pattern

```python
from fastapi import HTTPException, status

try:
    result = await service.method(data)
except NotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except ConflictError as e:
    raise HTTPException(status_code=409, detail=str(e))
```

## Reference Files

- `/app/api/endpoints/example.py` — Example endpoint.
- `/app/services/example_service.py` — Example service.
- `/app/db/repositories/example_repository.py` — Example repository.
- `/app/schemas/example.py` — Example schemas.

## Required Checks

- [ ] Endpoint follows REST conventions.
- [ ] Service layer contains business logic.
- [ ] Repository handles data access.
- [ ] Pydantic schemas for validation.
- [ ] Error handling implemented.
- [ ] Type annotations complete.
- [ ] Tests written.
