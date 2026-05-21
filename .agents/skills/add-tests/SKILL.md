---
name: add-tests
description: Write comprehensive tests for modules following project testing conventions. Use when adding new features or improving coverage.
---

# Add Tests Skill

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

Create thorough tests that verify functionality, catch regressions, and document expected behavior.

## Workflow

### Phase 1: Explore

1. Read the module to test in `/app/`.
2. Check existing tests in `/tests/` for patterns.
3. Identify all public methods/functions.
4. Find edge cases and error conditions.
5. Check for existing fixtures in `/tests/conftest.py`.

### Phase 2: Plan

Write a test plan:

1. List all functions/methods to test.
2. Identify test categories (unit, integration).
3. Plan test cases for each:
   - Happy path
   - Edge cases
   - Error conditions
   - Boundary values
4. Identify mocks needed.

Example plan:

```
Test Plan: BookingService

Unit Tests:
- test_create_booking_success
- test_create_booking_slot_not_available
- test_create_booking_invalid_email
- test_get_booking_by_id_found
- test_get_booking_by_id_not_found

Integration Tests:
- test_create_booking_end_to_end
- test_concurrent_bookings_handling

Mocks needed:
- BookingRepository
- Redis cache
```

### Phase 3: Code

#### Step 1: Create Test File

```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /tests/services/test_booking_service.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from app.services.booking_service import BookingService
from app.domain.booking import Booking
from app.exceptions import SlotNotAvailableError, InvalidEmailError

@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    repo.is_slot_available = AsyncMock(return_value=True)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo

@pytest.fixture
def booking_service(mock_repository):
    return BookingService(mock_repository)

class TestBookingServiceCreate:
    """Tests for BookingService.create_booking method."""
    
    async def test_create_booking_success(self, booking_service, mock_repository):
        """Test successful booking creation."""
        # Arrange
        slot_start = datetime(2025, 1, 15, 10, 0)
        customer_name = "John Doe"
        customer_email = "john@example.com"
        
        expected_booking = Booking(
            id=1,
            slot_start=slot_start,
            customer_name=customer_name,
            customer_email=customer_email,
            status="pending",
            created_at=datetime.utcnow()
        )
        mock_repository.create.return_value = expected_booking
        
        # Act
        result = await booking_service.create_booking(slot_start, customer_name, customer_email)
        
        # Assert
        assert result.id == expected_booking.id
        assert result.slot_start == slot_start
        mock_repository.is_slot_available.assert_called_once_with(slot_start)
        mock_repository.create.assert_called_once()
    
    async def test_create_booking_slot_not_available(self, booking_service, mock_repository):
        """Test booking creation when slot is taken."""
        # Arrange
        slot_start = datetime(2025, 1, 15, 10, 0)
        mock_repository.is_slot_available.return_value = False
        
        # Act & Assert
        with pytest.raises(SlotNotAvailableError):
            await booking_service.create_booking(slot_start, "John", "john@example.com")
        
        mock_repository.create.assert_not_called()
    
    async def test_create_booking_invalid_email(self, booking_service):
        """Test booking creation with invalid email."""
        # Arrange
        slot_start = datetime(2025, 1, 15, 10, 0)
        invalid_email = "not-an-email"
        
        # Act & Assert
        with pytest.raises(InvalidEmailError):
            await booking_service.create_booking(slot_start, "John", invalid_email)
```

#### Step 2: Add Integration Tests

```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /tests/api/test_booking.py
import pytest
from httpx import AsyncClient
from datetime import datetime

@pytest.mark.asyncio
async def test_create_booking_endpoint(client: AsyncClient):
    """Test booking creation through API."""
    # Arrange
    payload = {
        "slot_start": "2025-01-15T10:00:00",
        "customer_name": "John Doe",
        "customer_email": "john@example.com"
    }
    
    # Act
    response = await client.post("/api/bookings", json=payload)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["slot_start"] == "2025-01-15T10:00:00"
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_create_booking_conflict(client: AsyncClient):
    """Test booking creation for already booked slot."""
    # Arrange
    payload = {
        "slot_start": "2025-01-15T10:00:00",
        "customer_name": "Jane Doe",
        "customer_email": "jane@example.com"
    }
    
    # First booking succeeds
    await client.post("/api/bookings", json=payload)
    
    # Act: Second booking should fail
    response = await client.post("/api/bookings", json=payload)
    
    # Assert
    assert response.status_code == 409
    assert "not available" in response.json()["detail"]
```

#### Step 3: Add Fixtures

```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /tests/conftest.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.db.session import get_db_session

@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_booking_data():
    """Sample booking data for tests."""
    return {
        "slot_start": datetime(2025, 1, 15, 10, 0),
        "customer_name": "Test User",
        "customer_email": "test@example.com"
    }
```

### Phase 4: Verify

1. Run `make test` — ensure all tests pass.
2. Check coverage: `make coverage-html`.
3. Ensure >80% coverage for modified modules.
4. Run tests in isolation to verify no dependencies.

## What NOT to Do

- ❌ Do NOT write tests that depend on execution order.
- ❌ Do NOT mock everything (test real logic).
- ❌ Do NOT test implementation details (test behavior).
- ❌ Do NOT skip edge cases and error conditions.
- ❌ Do NOT write tests that are fragile (brittle assertions).

## Test Patterns

### Arrange-Act-Assert

```python
async def test_example(self):
    # Arrange
    input_data = {...}
    expected_result = {...}
    
    # Act
    result = await service.method(input_data)
    
    # Assert
    assert result == expected_result
```

### Parametrized Tests

```python
@pytest.mark.parametrize("email,expected", [
    ("valid@example.com", True),
    ("invalid", False),
    ("no-at-sign.com", False),
])
async def test_email_validation(self, email, expected):
    ...
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_method():
    result = await async_service.method()
    assert result is not None
```

## Reference Files

- `/tests/services/test_example_service.py` — Example service tests.
- `/tests/api/test_example.py` — Example API tests.
- `/tests/conftest.py` — Shared fixtures.

## Required Checks

- [ ] All tests pass.
- [ ] Coverage >80% for modified code.
- [ ] Tests are independent (can run in any order).
- [ ] Error cases are tested.
- [ ] Edge cases are covered.
- [ ] No flaky tests.
