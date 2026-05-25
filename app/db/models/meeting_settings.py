from sqlalchemy import Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.schemas.booking import MeetingDurationMinutes, MeetingProvider, MeetingTimezone


class MeetingSettings(Base):
    __tablename__ = "meeting_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
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
