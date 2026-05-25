from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from uuid import uuid4


def _next_half_hour_utc_naive(now_utc: datetime) -> datetime:
    rounded = (now_utc + timedelta(minutes=30)).replace(second=0, microsecond=0)
    return rounded + timedelta(minutes=(30 - rounded.minute % 30) % 30)


def main() -> None:
    slot_start = _next_half_hour_utc_naive(datetime.now(tz=timezone.utc))
    slot_start_naive = slot_start.replace(tzinfo=None)
    from_ts = slot_start_naive.replace(hour=0, minute=0)
    payload = {
        "slot_start": slot_start_naive.isoformat(),
        "from_ts": from_ts.isoformat(),
        "email_suffix": uuid4().hex[:8],
        "budget_slot_start": (slot_start_naive + timedelta(minutes=30)).isoformat(),
    }
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
