from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile


def run(cmd: list[str], env: dict[str, str]) -> None:
    subprocess.run(cmd, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    versions_dir = repo_root / "alembic" / "versions"
    before = {item.name for item in versions_dir.glob("*.py")}

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_url = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'drift_check.db'}"
        env = os.environ.copy()
        env["DATABASE_URL"] = db_url

        run(["alembic", "upgrade", "head"], env)
        run(["alembic", "revision", "--autogenerate", "-m", "drift-check"], env)

    after = {item.name for item in versions_dir.glob("*.py")}
    created = sorted(after - before)
    if len(created) != 1:
        raise SystemExit("Drift check expected exactly one generated revision")

    created_path = versions_dir / created[0]
    content = created_path.read_text()
    created_path.unlink()

    if "pass" not in content:
        raise SystemExit("Migration drift detected: autogenerate produced schema changes")

    print("Migration drift check passed")


if __name__ == "__main__":
    main()
