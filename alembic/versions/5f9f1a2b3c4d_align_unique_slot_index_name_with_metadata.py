"""align unique slot_start index name with metadata

Revision ID: 5f9f1a2b3c4d
Revises: 8b2c9a4d1f20
Create Date: 2026-05-25 18:20:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5f9f1a2b3c4d"
down_revision: Union[str, Sequence[str], None] = "8b2c9a4d1f20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Why: metadata defines a unique index name generated from the ORM field,
    # so aligning DB index naming removes noisy autogenerate drift in CI.
    op.drop_index("ux_bookings_slot_start", table_name="bookings")
    op.create_index(op.f("ix_bookings_slot_start"), "bookings", ["slot_start"], unique=True)


def downgrade() -> None:
    # Why: downgrade restores prior index naming expected by earlier revisions.
    op.drop_index(op.f("ix_bookings_slot_start"), table_name="bookings")
    op.create_index("ux_bookings_slot_start", "bookings", ["slot_start"], unique=True)
