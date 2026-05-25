from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.schemas.booking import BookingStatus, MeetingDurationMinutes, MeetingProvider, MeetingTimezone


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slot_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        index=True,
        unique=True,
    )
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
        default=MeetingProvider.GOOGLE_MEET,
    )
    meeting_timezone: Mapped[MeetingTimezone] = mapped_column(
        Enum(MeetingTimezone, native_enum=False),
        nullable=False,
        default=MeetingTimezone.ASIA_YEKATERINBURG,
    )
    meeting_duration_minutes: Mapped[MeetingDurationMinutes] = mapped_column(
        Enum(MeetingDurationMinutes, native_enum=False),
        nullable=False,
        default=MeetingDurationMinutes.THIRTY,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
