---
name: debug-failing-test
description: Diagnose root cause of failing tests through systematic investigation. Use when tests fail unexpectedly.
---

# Debug Failing Test Skill

## Purpose

Identify why a test is failing by gathering evidence, forming hypotheses, and testing them systematically.

## Workflow

### Phase 1: Explore

1. Run the failing test to see exact error.
2. Read the test code carefully.
3. Read the code being tested.
4. Check recent changes to both files.

```bash
# Run specific test
pytest tests/services/test_booking.py::test_create_booking -v

# Run with output
pytest tests/services/test_booking.py -v -s

# Run with coverage
pytest tests/services/test_booking.py --cov=app/services
```

### Phase 2: Gather Evidence

#### Step 1: Analyze Error Message

```
FAILED tests/services/test_booking.py::test_create_booking - AssertionError
Expected: BookingStatus.PENDING
Actual: None
```

Key questions:
- What assertion failed?
- What was expected vs actual?
- At what line did it fail?

#### Step 2: Check Test Setup

```python
# Is the mock configured correctly?
@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    # Does this return the right type?
    repo.create.return_value = expected_booking
    return repo
```

#### Step 3: Check Code Under Test

```python
# Does the service method actually set status?
async def create_booking(self, ...) -> Booking:
    booking = Booking(...)
    # Is status being set here?
    return await self.repository.create(booking)
```

### Phase 3: Form Hypotheses

List possible causes:

```markdown
Hypothesis 1: Mock not returning correct data
- Probability: HIGH
- Test: Print mock return value

Hypothesis 2: Service not setting status field
- Probability: MEDIUM  
- Test: Add debug log in service

Hypothesis 3: Pydantic model dropping field
- Probability: LOW
- Test: Check model config
```

### Phase 4: Test Hypotheses

#### Method 1: Add Temporary Logging

```python
async def test_create_booking(self, booking_service, mock_repository):
    result = await booking_service.create_booking(...)
    print(f"DEBUG: result.status = {result.status}")  # Add temporarily
    assert result.status == BookingStatus.PENDING
```

#### Method 2: Use Debugger

```python
import pytest

async def test_create_booking(self, booking_service, mock_repository):
    result = await booking_service.create_booking(...)
    pytest.breakpoint()  # Drops into pdb
    assert result.status == BookingStatus.PENDING
```

Run with: `pytest ... -s`

#### Method 3: Isolate the Issue

```python
# Minimal reproduction
async def test_minimal():
    booking = Booking(
        slot_start=datetime.now(),
        customer_name="Test",
        customer_email="test@example.com"
    )
    print(f"Booking status: {booking.status}")  # Check default
```

### Phase 5: Fix and Verify

Once root cause found:

1. Fix the underlying issue (not just the test).
2. Remove temporary debug code.
3. Run full test suite.
4. Verify fix doesn't break other tests.

## Common Patterns

### Pattern 1: Async/Await Issues

```python
# WRONG: Missing await
result = service.async_method()  # Returns coroutine

# RIGHT
result = await service.async_method()
```

### Pattern 2: Mock Configuration

```python
# WRONG: Mock returns MagicMock, not expected object
repo.create.return_value = None

# RIGHT
expected = Booking(id=1, ...)
repo.create.return_value = expected
```

### Pattern 3: Fixture Scope

```python
# WRONG: Using mutable default in fixture
@pytest.fixture
def booking_data():
    return {"status": "pending"}  # Shared across tests!

# RIGHT
@pytest.fixture
def booking_data():
    return {"status": "pending"}.copy()
```

### Pattern 4: Database State

```python
# WRONG: Tests depend on execution order
# Test 1 creates booking
# Test 2 expects no bookings

# RIGHT: Each test cleans up or uses transactions
@pytest.fixture
async def clean_db(db_session):
    yield db_session
    await db_session.rollback()
```

### Pattern 5: Timezone Issues

```python
# WRONG: Comparing naive and aware datetimes
expected = datetime(2025, 1, 15, 10, 0)  # Naive
actual = datetime.now(timezone.utc)  # Aware

# RIGHT: Both timezone-aware
expected = datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc)
```

## Debug Commands

```bash
# Run single test
pytest tests/path/test_file.py::test_name -v

# Stop on first failure
pytest tests/path/ -x

# Show local variables on failure
pytest tests/path/ -l

# Run until first failure (for flaky tests)
pytest tests/path/ --maxfail=1

# Show print statements
pytest tests/path/ -s

# Run with pdb on failure
pytest tests/path/ --pdb
```

## What NOT to Do

- ❌ Do NOT change test to match broken code.
- ❌ Do NOT remove assertions that fail.
- ❌ Do NOT ignore intermittent failures.
- ❌ Do NOT fix only the test without understanding root cause.
- ❌ Do NOT leave debug code in production.

## Reference Files

- `/tests/` — Test patterns.
- `/app/` — Source code.
- `/pytest.ini` — Pytest configuration.

## Required Checks

- [ ] Root cause identified.
- [ ] Fix addresses root cause, not symptom.
- [ ] All tests pass after fix.
- [ ] No debug code left behind.
- [ ] Similar issues checked in other tests.
