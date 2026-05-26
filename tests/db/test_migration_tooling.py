import os
from pathlib import Path
import subprocess
import sys
import tempfile

from sqlalchemy import create_engine, text


def test_migration_drift_check_script_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/migration_drift_check.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Migration drift check passed" in result.stdout


def test_migration_smoke_script_passes() -> None:
    result = subprocess.run(
        ["bash", "scripts/migration_smoke.sh"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Migration smoke passed" in result.stdout


def test_downgrade_handles_per_colleague_slot_collisions() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_url_async = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'collision.db'}"
        env = os.environ.copy()
        env["DATABASE_URL"] = db_url_async

        upgrade = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=repo_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert upgrade.returncode == 0, upgrade.stderr

        engine = create_engine(db_url_async.replace("+aiosqlite", ""))
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO bookings(
                        slot_start, customer_name, customer_email, status,
                        meeting_provider, meeting_timezone, meeting_duration_minutes, colleague_id
                    ) VALUES
                        (:slot_start, :name1, :email1, :status, :provider, :timezone, :duration, :colleague1),
                        (:slot_start, :name2, :email2, :status, :provider, :timezone, :duration, :colleague2)
                    """
                ),
                {
                    "slot_start": "2026-01-06 10:00:00",
                    "name1": "Collision A",
                    "email1": "collision-a@example.com",
                    "name2": "Collision B",
                    "email2": "collision-b@example.com",
                    "status": "PENDING",
                    "provider": "GOOGLE_MEET",
                    "timezone": "UTC",
                    "duration": "THIRTY",
                    "colleague1": 1,
                    "colleague2": 2,
                },
            )

        downgrade = subprocess.run(
            ["alembic", "downgrade", "base"],
            cwd=repo_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert downgrade.returncode == 0, downgrade.stderr
