import json
import subprocess
import sys
from datetime import datetime


def test_generate_smoke_payload_uses_future_30_minute_slots() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/generate_smoke_booking_payload.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    slot_start = datetime.fromisoformat(payload["slot_start"])
    from_ts = datetime.fromisoformat(payload["from_ts"])
    budget_slot_start = datetime.fromisoformat(payload["budget_slot_start"])

    assert slot_start.tzinfo is None
    assert slot_start.second == 0
    assert slot_start.microsecond == 0
    assert slot_start.minute in {0, 30}
    assert from_ts == slot_start.replace(hour=0, minute=0)
    assert (budget_slot_start - slot_start).total_seconds() == 30 * 60
    assert len(payload["email_suffix"]) == 8
