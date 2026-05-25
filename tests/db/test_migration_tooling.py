import subprocess
import sys


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
