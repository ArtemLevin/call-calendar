#!/usr/bin/env bash
set -euo pipefail

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

DB_PATH="$TMP_DIR/migration_smoke.db"
DB_URL="sqlite+aiosqlite:///$DB_PATH"
export DATABASE_URL="$DB_URL"

# Why: smoke must validate real migration chain behavior, not ORM create_all shortcuts.
alembic upgrade head >/dev/null

python3 - <<'PY'
import os
from sqlalchemy import create_engine, inspect, text

db_url = os.environ["DATABASE_URL"].replace("+aiosqlite", "")
engine = create_engine(db_url)

with engine.connect() as conn:
    tables = inspect(conn).get_table_names()
    if "bookings" not in tables:
        raise SystemExit("Missing bookings table after upgrade head")
    if "colleagues" not in tables:
        raise SystemExit("Missing colleagues table after upgrade head")

    conn.execute(
        text(
            """
            INSERT INTO bookings(slot_start, customer_name, customer_email, status, meeting_provider, meeting_timezone, meeting_duration_minutes, colleague_id)
            VALUES (:slot_start, :customer_name, :customer_email, :status, :meeting_provider, :meeting_timezone, :meeting_duration_minutes, :colleague_id)
            """
        ),
        {
            "slot_start": "2026-01-01 10:00:00",
            "customer_name": "Smoke",
            "customer_email": "smoke@example.com",
            "status": "PENDING",
            "meeting_provider": "GOOGLE_MEET",
            "meeting_timezone": "UTC",
            "meeting_duration_minutes": "THIRTY",
            "colleague_id": 1,
        },
    )
    conn.commit()

    count = conn.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one()
    if count < 1:
        raise SystemExit("Expected at least one booking row after insert")

    indexes = {item["name"] for item in inspect(conn).get_indexes("bookings")}
    if "ix_bookings_colleague_id" not in indexes:
        raise SystemExit("Missing colleague_id index after migrations")

    unique_constraints = {item["name"] for item in inspect(conn).get_unique_constraints("bookings")}
    if "uq_bookings_colleague_slot_start" not in unique_constraints:
        raise SystemExit("Missing per-colleague unique slot constraint after migrations")
PY

# Why: one-step rollback/forward cycle catches broken downgrade scripts early.
alembic downgrade 5f9f1a2b3c4d >/dev/null
alembic upgrade head >/dev/null

echo "Migration smoke passed"
