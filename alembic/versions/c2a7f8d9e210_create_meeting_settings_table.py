"""create meeting settings table

Revision ID: c2a7f8d9e210
Revises: 9c1d4e7f2a10
Create Date: 2026-05-25 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c2a7f8d9e210"
down_revision: str | None = "9c1d4e7f2a10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "meeting_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "meeting_provider",
            sa.Enum("GOOGLE_MEET", "ZOOM", "PHONE", name="meetingprovider", native_enum=False),
            nullable=False,
        ),
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
        ),
        sa.Column(
            "meeting_duration_minutes",
            sa.Enum("THIRTY", name="meetingdurationminutes", native_enum=False),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("meeting_settings")
