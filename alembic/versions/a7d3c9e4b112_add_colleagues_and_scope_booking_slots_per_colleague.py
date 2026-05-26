"""add colleagues and scope booking slots per colleague

Revision ID: a7d3c9e4b112
Revises: 5f9f1a2b3c4d
Create Date: 2026-05-26 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a7d3c9e4b112"
down_revision: Union[str, Sequence[str], None] = "5f9f1a2b3c4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "colleagues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("default_meeting_provider", sa.Enum("GOOGLE_MEET", "ZOOM", "PHONE", name="meetingprovider", native_enum=False), nullable=False),
        sa.Column("timezone", sa.Enum("ASIA_YEKATERINBURG", "UTC", "EUROPE_BERLIN", "AMERICA_NEW_YORK", name="meetingtimezone", native_enum=False), nullable=False),
        sa.Column("meeting_duration_minutes", sa.Enum("THIRTY", name="meetingdurationminutes", native_enum=False), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_colleagues_id"), "colleagues", ["id"], unique=False)
    op.execute(
        """
        INSERT INTO colleagues (id, name, default_meeting_provider, timezone, meeting_duration_minutes)
        VALUES (1, 'Kirill Mokevnin', 'GOOGLE_MEET', 'ASIA_YEKATERINBURG', 'THIRTY')
        """
    )

    with op.batch_alter_table("bookings") as batch_op:
        batch_op.add_column(sa.Column("colleague_id", sa.Integer(), nullable=False, server_default="1"))
        batch_op.create_index(op.f("ix_bookings_colleague_id"), ["colleague_id"], unique=False)
        batch_op.drop_index(op.f("ix_bookings_slot_start"))
        batch_op.create_foreign_key(
            "fk_bookings_colleague_id_colleagues",
            "colleagues",
            ["colleague_id"],
            ["id"],
        )
        batch_op.create_unique_constraint("uq_bookings_colleague_slot_start", ["colleague_id", "slot_start"])


def downgrade() -> None:
    # Why: older schema enforces global unique(slot_start), so we must collapse
    # per-colleague duplicates before recreating that unique index in downgrade.
    op.execute(
        """
        DELETE FROM bookings
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM bookings
            GROUP BY slot_start
        )
        """
    )

    # Why: if a previous SQLite batch migration attempt crashed, the temporary
    # table can remain and block retry of clean-db/downgrade with
    # "_alembic_tmp_bookings already exists".
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_bookings")

    with op.batch_alter_table("bookings") as batch_op:
        batch_op.drop_constraint("uq_bookings_colleague_slot_start", type_="unique")
        batch_op.drop_constraint("fk_bookings_colleague_id_colleagues", type_="foreignkey")
        batch_op.create_index(op.f("ix_bookings_slot_start"), ["slot_start"], unique=True)
        batch_op.drop_index(op.f("ix_bookings_colleague_id"))
        batch_op.drop_column("colleague_id")

    op.drop_index(op.f("ix_colleagues_id"), table_name="colleagues")
    op.drop_table("colleagues")
