"""add meeting metadata to bookings

Revision ID: 9c1d4e7f2a10
Revises: 5f9f1a2b3c4d
Create Date: 2026-05-25 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9c1d4e7f2a10"
down_revision: str | None = "5f9f1a2b3c4d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column(
            "meeting_provider",
            sa.Enum("GOOGLE_MEET", "ZOOM", "PHONE", name="meetingprovider", native_enum=False),
            nullable=False,
            server_default="GOOGLE_MEET",
        ),
    )
    op.add_column(
        "bookings",
        sa.Column(
            "meeting_timezone",
            sa.Enum(
                "ASIA_YEKATERINBURG",
                "UTC",
                "EUROPE_BERLIN",
                "AMERICA_NEW_YORK",
                name="meetingtimezone",
                native_enum=False,
            ),
            nullable=False,
            server_default="ASIA_YEKATERINBURG",
        ),
    )
    op.add_column(
        "bookings",
        sa.Column(
            "meeting_duration_minutes",
            sa.Enum("THIRTY", name="meetingdurationminutes", native_enum=False),
            nullable=False,
            server_default="THIRTY",
        ),
    )


def downgrade() -> None:
    op.drop_column("bookings", "meeting_duration_minutes")
    op.drop_column("bookings", "meeting_timezone")
    op.drop_column("bookings", "meeting_provider")
