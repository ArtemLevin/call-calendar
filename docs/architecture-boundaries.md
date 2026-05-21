# Architecture Boundaries

## Layered Architecture (STRICT)

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│    /app/api (FastAPI endpoints)         │
├─────────────────────────────────────────┤
│            Service Layer                │
│    /app/services (Business logic)       │
├─────────────────────────────────────────┤
│          Repository Layer               │
│    /app/db/repositories (Data access)   │
├─────────────────────────────────────────┤
│           Database Layer                │
│    /app/db/models (SQLAlchemy ORM)      │
└─────────────────────────────────────────┘
```

## Dependency Direction

```
Endpoint → Service → Repository → Model
     ↓        ↓           ↓
  Schema  Exception   Session
```

**Dependencies flow inward. Never upward.**

---

## Prohibited Patterns

### ❌ Direct DB Access from Endpoint

```python
# WRONG - Endpoint accessing database directly
@router.post("/bookings")
async def create_booking(db: AsyncSession = Depends(get_db)):
    booking = Booking(...)
    db.add(booking)
    await db.commit()
```

```python
# RIGHT - Through service layer
@router.post("/bookings")
async def create_booking(
    data: BookingCreate,
    service: BookingService = Depends(get_booking_service)
):
    booking = await service.create_booking(data)
```

### ❌ Business Logic in Endpoint

```python
# WRONG - Business logic in endpoint
@router.post("/bookings")
async def create_booking(data: BookingCreate, db: AsyncSession):
    # Validation logic mixed with HTTP handling
    if "@" not in data.email:
        raise HTTPException(400, "Invalid email")
    
    # Availability check in endpoint
    result = await db.execute(select(Booking).where(...))
    if result.scalar():
        raise HTTPException(409, "Slot taken")
```

```python
# RIGHT - Business logic in service
# /app/services/booking_service.py
class BookingService:
    async def create_booking(self, data: BookingCreate) -> Booking:
        self.validator.validate_email(data.email)
        is_available = await self.repo.is_slot_available(data.slot_start)
        if not is_available:
            raise SlotNotAvailableError()
        return await self.repo.create(data)
```

### ❌ HTTP Requests from Model

```python
# WRONG - Model making HTTP requests
class Booking(Base):
    def send_confirmation(self):
        requests.post("https://email-service/...", json={...})
```

```python
# RIGHT - Service handles external calls
class BookingService:
    async def create_booking(self, data: BookingCreate) -> Booking:
        booking = await self.repo.create(data)
        await self.notification_service.send_confirmation(booking)
        return booking
```

### ❌ Bypassing Service Layer

```python
# WRONG - Repository called from endpoint
@router.get("/bookings/{id}")
async def get_booking(id: int, db: AsyncSession):
    repo = BookingRepository(db)
    booking = await repo.get_by_id(id)
```

```python
# RIGHT - Service mediates repository
@router.get("/bookings/{id}")
async def get_booking(
    id: int,
    service: BookingService = Depends(get_booking_service)
):
    booking = await service.get_by_id(id)
```

### ❌ Parallel Types/Entities

```python
# WRONG - Creating duplicate types
class BookingDTO(BaseModel):
    id: int
    slot_start: datetime

class BookingSchema(BaseModel):
    id: int
    slot_start: datetime

# Which one to use?
```

```python
# RIGHT - Single source of truth
class BookingResponse(BaseModel):
    """Standard response schema for bookings."""
    id: int
    slot_start: datetime
    customer_name: str
    customer_email: EmailStr
    status: BookingStatus
```

---

## Allowed Patterns

### ✅ Endpoint → Service → Repository

```python
# /app/api/endpoints/bookings.py
@router.post("/")
async def create_booking(
    data: BookingCreate,
    service: BookingService = Depends(get_booking_service)
) -> BookingResponse:
    booking = await service.create_booking(data)
    return BookingResponse.model_validate(booking)

# /app/services/booking_service.py
class BookingService:
    def __init__(self, repo: BookingRepository):
        self.repo = repo
    
    async def create_booking(self, data: BookingCreate) -> Booking:
        return await self.repo.create(data)

# /app/db/repositories/booking_repository.py
class BookingRepository:
    async def create(self, data: BookingCreate) -> Booking:
        booking = Booking(**data.model_dump())
        self.session.add(booking)
        await self.session.commit()
        return booking
```

### ✅ Pydantic for Validation

```python
from pydantic import BaseModel, EmailStr, Field, validator

class BookingCreate(BaseModel):
    slot_start: datetime
    customer_name: str = Field(min_length=2, max_length=255)
    customer_email: EmailStr
    
    @validator('slot_start')
    def slot_must_be_future(cls, v):
        if v < datetime.now():
            raise ValueError("Slot must be in the future")
        return v
```

### ✅ Custom Exceptions

```python
# /app/exceptions.py
class BookingNotFoundError(Exception):
    def __init__(self, booking_id: int):
        super().__init__(f"Booking {booking_id} not found")

class SlotNotAvailableError(Exception):
    def __init__(self, slot_start: datetime):
        super().__init__(f"Slot {slot_start} is not available")

# /app/api/endpoints/bookings.py
@router.post("/")
async def create_booking(data: BookingCreate, service: BookingService):
    try:
        return await service.create_booking(data)
    except BookingNotFoundError as e:
        raise HTTPException(404, str(e))
    except SlotNotAvailableError as e:
        raise HTTPException(409, str(e))
```

---

## Legacy Code Rules

### Identifying Legacy

Mark legacy code with comments:

```python
# TODO: Refactor - violates layered architecture
# This endpoint directly accesses database
@router.get("/legacy/bookings")
async def legacy_endpoint(db: AsyncSession):
    ...
```

### Working with Legacy

1. **Do NOT copy patterns** from legacy code
2. **Add tests** before refactoring
3. **Incremental improvement** preferred over rewrite
4. **Document** technical debt

### Migration Path

```
Legacy → Adapter → New Architecture

Step 1: Add tests around legacy code
Step 2: Create new service following architecture
Step 3: Use adapter to connect legacy to new
Step 4: Migrate callers incrementally
Step 5: Remove legacy when safe
```

---

## What Counts as Violation

| Pattern | Severity | Action |
|---------|----------|--------|
| Direct DB in endpoint | Critical | Block merge |
| Business logic in template | Critical | Block merge |
| Missing type hints | High | Request fix |
| No tests for new feature | High | Block merge |
| Skipping service layer | Critical | Block merge |
| Parallel types | Medium | Request consolidation |
| Large functions (>50 lines) | Medium | Suggest refactor |
| Missing docstrings | Low | Suggest addition |

---

## Enforcement

### Pre-commit Checks

```bash
# Run before commit
make lint        # Style violations
make typecheck   # Type errors
make test        # Test failures
```

### CI Pipeline

```yaml
# .github/workflows/ci.yml
- name: Architecture Check
  run: |
    make lint
    make typecheck
    make test
```

### Code Review

Reviewers must check:
- [ ] Architecture boundaries respected
- [ ] No short-circuit paths
- [ ] Tests cover new functionality
- [ ] Types are complete
