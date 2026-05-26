from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.schemas.booking import BookingStatus, MeetingDurationMinutes, MeetingProvider, MeetingTimezone


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("colleague_id", "slot_start", name="uq_bookings_colleague_slot_start"),)
    DEFAULT_PROVIDER = MeetingProvider.GOOGLE_MEET
    DEFAULT_TIMEZONE = MeetingTimezone.ASIA_YEKATERINBURG
    DEFAULT_DURATION = MeetingDurationMinutes.THIRTY

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slot_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
    )
    colleague_id: Mapped[int] = mapped_column(ForeignKey("colleagues.id"), nullable=False, index=True, default=1)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, native_enum=False),
        nullable=False,
        default=BookingStatus.PENDING,
    )
    meeting_provider: Mapped[MeetingProvider] = mapped_column(
        Enum(MeetingProvider, native_enum=False),
        nullable=False,
        default=DEFAULT_PROVIDER,
    )
    meeting_timezone: Mapped[MeetingTimezone] = mapped_column(
        Enum(MeetingTimezone, native_enum=False),
        nullable=False,
        default=DEFAULT_TIMEZONE,
    )
    meeting_duration_minutes: Mapped[MeetingDurationMinutes] = mapped_column(
        Enum(MeetingDurationMinutes, native_enum=False),
        nullable=False,
        default=DEFAULT_DURATION,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
