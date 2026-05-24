"""add unique slot_start constraint

Revision ID: 1e4f3c2a9b11
Revises: 97012b799b9a
Create Date: 2026-05-23 18:10:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1e4f3c2a9b11"
down_revision: Union[str, Sequence[str], None] = "97012b799b9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Why: only a database-level uniqueness guarantee can prevent double booking
    # when concurrent requests race past application-level availability checks.
    op.create_index("ux_bookings_slot_start", "bookings", ["slot_start"], unique=True)


def downgrade() -> None:
    # Why: keeping rollback symmetrical preserves predictable deploy recovery if
    # this protection needs to be reverted during incident response.
    op.drop_index("ux_bookings_slot_start", table_name="bookings")
