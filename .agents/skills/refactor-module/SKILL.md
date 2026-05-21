---
name: refactor-module
description: Restructure and improve code quality without changing behavior. Use when improving maintainability or preparing for new features.
---

# Refactor Module Skill

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

Improve code structure, readability, and maintainability while preserving existing functionality.

## Workflow

### Phase 1: Explore

1. Read the module to refactor completely.
2. Understand all public interfaces (functions, classes).
3. Identify all callers/dependencies.
4. Check test coverage for this module.

```bash
# Find usages
rg -n "from app\.services\.booking" app tests
rg -n "import BookingService" app tests

# Run tests before refactoring
make test
```

### Phase 2: Plan

Write a refactoring plan:

```markdown
## Refactor Plan: BookingService

### Current Issues
1. Large class (300+ lines)
2. Mixed responsibilities (validation + business logic)
3. Deep nesting in methods
4. Missing type hints

### Proposed Structure
1. Extract validation to separate class
2. Split into smaller service methods
3. Add comprehensive type hints
4. Improve error handling

### Risk Mitigation
- Keep tests passing throughout
- Small incremental changes
- Verify after each step
```

### Phase 3: Code

#### Step 1: Extract Validation Logic

**Before:**
```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /app/services/booking_service.py
class BookingService:
    async def create_booking(self, slot_start, customer_name, customer_email):
        # Validation mixed with business logic
        if not customer_email or "@" not in customer_email:
            raise ValueError("Invalid email")
        
        if not customer_name or len(customer_name) < 2:
            raise ValueError("Name too short")
        
        # More validation...
        
        # Business logic
        available = await self.repo.is_slot_available(slot_start)
        if not available:
            raise SlotNotAvailableError()
        
        booking = Booking(...)
        return await self.repo.create(booking)
```

**After:**
```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /app/services/validators/booking_validator.py
from app.exceptions import InvalidEmailError, InvalidNameError

class BookingValidator:
    """Validates booking input data."""
    
    @staticmethod
    def validate_email(email: str) -> None:
        """Validate email format."""
        if not email or "@" not in email or "." not in email.split("@")[-1]:
            raise InvalidEmailError(f"Invalid email format: {email}")
    
    @staticmethod
    def validate_name(name: str) -> None:
        """Validate customer name."""
        if not name or len(name.strip()) < 2:
            raise InvalidNameError(f"Name must be at least 2 characters: {name}")

# /app/services/booking_service.py
from app.services.validators.booking_validator import BookingValidator

class BookingService:
    def __init__(self, repository: BookingRepository):
        self.repository = repository
        self.validator = BookingValidator()
    
    async def create_booking(
        self,
        slot_start: datetime,
        customer_name: str,
        customer_email: str
    ) -> Booking:
        """Create a new booking after validation."""
        # Validate input
        self.validator.validate_email(customer_email)
        self.validator.validate_name(customer_name)
        
        # Check availability
        is_available = await self._check_slot_availability(slot_start)
        if not is_available:
            raise SlotNotAvailableError(slot_start)
        
        # Create booking
        return await self._create_booking_record(
            slot_start, customer_name, customer_email
        )
    
    async def _check_slot_availability(self, slot_start: datetime) -> bool:
        """Check if slot is available for booking."""
        return await self.repository.is_slot_available(slot_start)
    
    async def _create_booking_record(
        self,
        slot_start: datetime,
        customer_name: str,
        customer_email: str
    ) -> Booking:
        """Create booking record in database."""
        booking = Booking(
            slot_start=slot_start,
            customer_name=customer_name,
            customer_email=customer_email,
            status=BookingStatus.PENDING
        )
        return await self.repository.create(booking)
```

#### Step 2: Apply SOLID Principles

**Single Responsibility:**
- Each class has one reason to change
- Validation separated from business logic
- Data access separated from business rules

**Open/Closed:**
- New validators can be added without modifying existing ones
- Extension through composition

**Liskov Substitution:**
- Interfaces are clear and consistent
- Subclasses can replace parents

**Interface Segregation:**
- Small, focused interfaces
- No forced dependencies

**Dependency Inversion:**
- Depend on abstractions (interfaces)
- Inject dependencies

#### Step 3: Improve Type Hints

```python
# Before
def process(data):
    ...

# After
from typing import Optional
from datetime import datetime
from app.schemas.booking import BookingCreate

async def process_booking_request(
    data: BookingCreate,
    timezone: Optional[str] = None
) -> BookingResponse:
    ...
```

### Phase 4: Verify

1. Run all tests: `make test`
2. Check linting: `make lint`
3. Verify types: `make typecheck`
4. Manual testing of affected features
5. Performance check (if applicable)

## What NOT to Do

- ❌ Do NOT change behavior during refactoring.
- ❌ Do NOT refactor without tests.
- ❌ Do NOT make large changes in single commit.
- ❌ Do NOT ignore performance implications.
- ❌ Do NOT remove working code without understanding why it exists.

## Refactoring Patterns

### Pattern 1: Extract Method

```python
# Before
def process_order(order):
    # 50 lines of code doing multiple things
    ...

# After
def process_order(order):
    validate_order(order)
    calculate_totals(order)
    apply_discounts(order)
    save_order(order)
```

### Pattern 2: Replace Conditional with Polymorphism

```python
# Before
def get_price(customer_type):
    if customer_type == "regular":
        return price * 1.0
    elif customer_type == "vip":
        return price * 0.9
    elif customer_type == "wholesale":
        return price * 0.7

# After
class PricingStrategy(ABC):
    @abstractmethod
    def get_price(self, base_price: float) -> float:
        pass

class RegularPricing(PricingStrategy):
    def get_price(self, base_price: float) -> float:
        return base_price

class VIPPricing(PricingStrategy):
    def get_price(self, base_price: float) -> float:
        return base_price * 0.9
```

### Pattern 3: Introduce Parameter Object

```python
# Before
def create_booking(start, end, name, email, phone, notes):
    ...

# After
def create_booking(booking_data: BookingCreate):
    ...
```

## Reference Files

- `/app/services/` — Service layer examples.
- `/tests/` — Test patterns for verification.

## Required Checks

- [ ] All tests pass.
- [ ] Behavior unchanged.
- [ ] Code is more readable.
- [ ] SOLID principles applied.
- [ ] Type hints complete.
- [ ] Documentation updated.

## Definition of Done (DoD)

- [ ] Scope of change is implemented and matches the agreed plan for this skill task.
- [ ] Tests for new/changed behavior are added or updated (happy path, edge cases, and error conditions as applicable).
- [ ] `make test`, `make lint`, and `make typecheck` have been run, and failures are resolved or explicitly documented.
- [ ] Documentation is added/updated when behavior, API contracts, or operational workflow changed.
- [ ] Layered architecture remains valid: Endpoint → Service → Repository (no bypassing service layer).
- [ ] Type annotations and validation are present for new/changed public interfaces.
- [ ] Final diff is reviewed for unintended changes (no dead code, commented-out debug code, or unrelated edits).
