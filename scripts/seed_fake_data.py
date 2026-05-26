from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta
import random

from faker import Faker
from sqlalchemy import delete, select

from app.db.models.booking import Booking
from app.db.models.colleague import Colleague
from app.db.models.meeting_settings import MeetingSettings
from app.db.session import AsyncSessionLocal
from app.schemas.booking import BookingStatus, MeetingDurationMinutes, MeetingProvider, MeetingTimezone


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Populate database with fake colleagues and bookings")
    parser.add_argument("--colleagues", type=int, default=6, help="Number of colleagues to ensure in DB")
    parser.add_argument("--days", type=int, default=21, help="How many upcoming days to generate")
    parser.add_argument("--bookings-per-colleague", type=int, default=24, help="Bookings to create per colleague")
    parser.add_argument("--reset", action="store_true", help="Delete existing bookings and non-default colleagues before seeding")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible fixtures")
    return parser


async def _seed(colleagues: int, days: int, bookings_per_colleague: int, reset: bool, seed: int) -> None:
    faker = Faker()
    Faker.seed(seed)
    random.seed(seed)

    async with AsyncSessionLocal() as session:
        if reset:
            # Why: reset keeps repeated seeding deterministic for manual QA scenarios.
            await session.execute(delete(Booking))
            await session.execute(delete(Colleague).where(Colleague.id != 1))
            await session.execute(delete(MeetingSettings))
            await session.commit()

        existing = list((await session.execute(select(Colleague).order_by(Colleague.id.asc()))).scalars().all())
        next_id = (existing[-1].id + 1) if existing else 1

        providers = list(MeetingProvider)
        timezones = list(MeetingTimezone)

        while len(existing) < colleagues:
            colleague = Colleague(
                id=next_id,
                name=faker.name(),
                default_meeting_provider=random.choice(providers),
                timezone=random.choice(timezones),
                meeting_duration_minutes=MeetingDurationMinutes.THIRTY,
            )
            session.add(colleague)
            existing.append(colleague)
            next_id += 1

        await session.commit()

        colleague_ids = [item.id for item in existing]
        status_pool = [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.COMPLETED]

        start_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        slot_candidates: list[datetime] = []
        for day_offset in range(days):
            current_day = start_day + timedelta(days=day_offset)
            if current_day.weekday() >= 5:
                continue
            for hour in range(9, 18):
                slot_candidates.append(current_day.replace(hour=hour, minute=0))
                slot_candidates.append(current_day.replace(hour=hour, minute=30))

        created = 0
        for colleague_id in colleague_ids:
            chosen_slots = random.sample(slot_candidates, k=min(bookings_per_colleague, len(slot_candidates)))
            for slot_start in chosen_slots:
                booking = Booking(
                    slot_start=slot_start,
                    colleague_id=colleague_id,
                    customer_name=faker.name(),
                    customer_email=faker.email(),
                    status=random.choice(status_pool),
                    meeting_provider=random.choice(providers),
                    meeting_timezone=random.choice(timezones),
                    meeting_duration_minutes=MeetingDurationMinutes.THIRTY,
                )
                session.add(booking)
                created += 1

        await session.commit()
        print(f"Seeded colleagues={len(colleague_ids)} bookings={created}")


def main() -> None:
    args = _build_parser().parse_args()
    asyncio.run(_seed(args.colleagues, args.days, args.bookings_per_colleague, args.reset, args.seed))


if __name__ == "__main__":
    main()
