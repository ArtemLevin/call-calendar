---
name: db-migration
description: Plan and execute database migrations safely. Use when schema changes are required.
---

# DB Migration Skill

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



## Quick start (5 шагов)

1. Проверить структуру репозитория и ключевые пути (`rg --files`, директории `app/tests/alembic`).
2. Определить целевой scope: какие файлы/методы/сценарии меняются.
3. Выполнить минимальный сценарий этого skill (по фазам Explore → Plan → Code → Verify).
4. Проверить результат локально (`make test`, `make lint`, `make typecheck` при применимости).
5. Сверить итог с `Definition of Done (DoD)` перед PR/merge.

## Common pitfalls

- Пропуск шага проверки путей и слепое копирование path-based примеров.
- Фокус только на happy path без edge/error/conflict сценариев.
- Нарушение архитектурных границ (обход слоя Service или смешение ответственности).
- Отсутствие обновления тестов/документации при изменении поведения/API.
- Оставленные временные артефакты (debug-код, лишние правки, неочищенный diff).


## Purpose

Safely modify database schema while preserving data and maintaining backward compatibility during deployment.

## Workflow

### Phase 1: Explore

1. Read current schema in `/app/db/models/`.
2. Check existing migrations in `/alembic/versions/`.
3. Understand the required change.
4. Identify dependent code (services, repositories).

### Phase 2: Plan

Write a migration plan:

```markdown
## Migration Plan: Add booking status field

### Current State
- Table: bookings
- Columns: id, slot_start, customer_name, customer_email, created_at

### Target State
- Add column: status (VARCHAR, not null, default='pending')
- Add index: idx_bookings_status

### Migration Strategy
1. Add column with default value (non-breaking)
2. Backfill existing rows (if needed)
3. Update application code
4. Deploy
5. Optional: Remove default constraint

### Rollback Plan
- Drop column if issues arise
- Previous app version remains compatible

### Risk Assessment
- Risk: LOW (additive change)
- Downtime: NONE
- Data loss: NONE
```

### Phase 3: Code

#### Step 1: Create Alembic Migration

```bash
alembic revision -m "add_status_to_bookings"
```

#### Step 2: Edit Migration File

```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /alembic/versions/001_add_status_to_bookings.py
"""add status to bookings

Revision ID: abc123def456
Revises: previous_revision_id
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123def456'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add status column to bookings table."""
    # Add column with default value (safe for existing rows)
    op.add_column(
        'bookings',
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending')
    )
    
    # Create index for efficient filtering
    op.create_index('idx_bookings_status', 'bookings', ['status'])
    
    # Remove server default after backfill (optional, can be separate migration)
    # op.alter_column('bookings', 'status', server_default=None)


def downgrade() -> None:
    """Remove status column from bookings table."""
    op.drop_index('idx_bookings_status', table_name='bookings')
    op.drop_column('bookings', 'status')
```

#### Step 3: Update Models

```python
# PSEUDOCODE (adapt paths to this repo if needed)
# /app/db/models/booking.py
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_start = Column(DateTime, nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default=BookingStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())
```

#### Step 4: Update Pydantic Schemas

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
    id: int
    slot_start: datetime
    customer_name: str
    customer_email: EmailStr
    status: BookingStatus
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Phase 4: Verify

1. Run migration on test database: `make migrate-test`
2. Verify schema: `alembic current`
3. Test rollback: `alembic downgrade -1`
4. Test forward again: `alembic upgrade head`
5. Run all tests: `make test`

## What NOT to Do

- ❌ Do NOT rename columns without deprecation period.
- ❌ Do NOT drop columns in same migration as adding replacement.
- ❌ Do NOT change column types without data migration plan.
- ❌ Do NOT run migrations without backup strategy.
- ❌ Do NOT skip testing rollback.

## Migration Patterns

### Additive Changes (Safe)

```python
# Adding column
op.add_column('table', sa.Column('new_col', sa.String(), nullable=True))

# Adding index
op.create_index('idx_table_col', 'table', ['col'])

# Adding table
op.create_table('new_table', ...)
```

### Breaking Changes (Require Care)

```python
# Renaming column (two-step process)
# Step 1: Add new column, keep old
op.add_column('table', sa.Column('new_name', ...))

# Step 2: After deploy, migrate data
# UPDATE table SET new_name = old_name WHERE new_name IS NULL

# Step 3: Next deployment, remove old column
op.drop_column('table', 'old_name')
```

### Data Migration

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('full_name', sa.String()))
    
    # Backfill data
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE users 
            SET full_name = CONCAT(first_name, ' ', last_name)
            WHERE full_name IS NULL
        """)
    )
    
    # Now make it not null
    op.alter_column('users', 'full_name', nullable=False)
```

## Reference Files

- `/alembic/versions/` — Existing migrations.
- `/app/db/models/` — SQLAlchemy models.
- `/app/schemas/` — Pydantic schemas.

## Required Checks

- [ ] Migration runs successfully.
- [ ] Rollback works.
- [ ] Tests pass with new schema.
- [ ] No data loss.
- [ ] Backward compatible during rollout.
- [ ] Indexes added for new queries.

## Definition of Done (DoD)

- [ ] Scope of change is implemented and matches the agreed plan for this skill task.
- [ ] Tests for new/changed behavior are added or updated (happy path, edge cases, and error conditions as applicable).
- [ ] `make test`, `make lint`, and `make typecheck` have been run, and failures are resolved or explicitly documented.
- [ ] Documentation is added/updated when behavior, API contracts, or operational workflow changed.
- [ ] Layered architecture remains valid: Endpoint → Service → Repository (no bypassing service layer).
- [ ] Type annotations and validation are present for new/changed public interfaces.
- [ ] Final diff is reviewed for unintended changes (no dead code, commented-out debug code, or unrelated edits).
