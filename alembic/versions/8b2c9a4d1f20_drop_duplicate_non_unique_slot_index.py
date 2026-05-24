"""drop duplicate non-unique slot_start index

Revision ID: 8b2c9a4d1f20
Revises: 1e4f3c2a9b11
Create Date: 2026-05-23 19:20:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8b2c9a4d1f20"
down_revision: Union[str, Sequence[str], None] = "1e4f3c2a9b11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Why: keeping both unique and non-unique indexes on the same column adds
    # write overhead without query benefits once uniqueness is already enforced.
    op.drop_index(op.f("ix_bookings_slot_start"), table_name="bookings")


def downgrade() -> None:
    # Why: rollback restores the historical index layout expected by prior
    # revisions so downgrade behavior remains deterministic.
    op.create_index(op.f("ix_bookings_slot_start"), "bookings", ["slot_start"], unique=False)
