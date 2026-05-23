"""create bookings table

Revision ID: 97012b799b9a
Revises:
Create Date: 2026-05-23 15:16:34.836852

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "97012b799b9a"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Why: table creation codifies booking persistence in schema form so every
    # environment enforces the same storage contract regardless of deploy order.
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slot_start", sa.DateTime(), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "CONFIRMED",
                "CANCELLED",
                "COMPLETED",
                name="bookingstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Why: read-oriented indexes are added at migration time to avoid production
    # latency spikes from retrofitting indexes after data volume has grown.
    op.create_index(op.f("ix_bookings_customer_email"), "bookings", ["customer_email"], unique=False)
    op.create_index(op.f("ix_bookings_id"), "bookings", ["id"], unique=False)
    op.create_index(op.f("ix_bookings_slot_start"), "bookings", ["slot_start"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Why: indexes are removed before dropping the table so rollback order stays
    # explicit and deterministic across database engines.
    op.drop_index(op.f("ix_bookings_slot_start"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_customer_email"), table_name="bookings")
    op.drop_table("bookings")
