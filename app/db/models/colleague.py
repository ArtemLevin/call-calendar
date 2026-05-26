from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.schemas.booking import MeetingDurationMinutes, MeetingProvider, MeetingTimezone


class Colleague(Base):
    __tablename__ = "colleagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_meeting_provider: Mapped[MeetingProvider] = mapped_column(
        Enum(MeetingProvider, native_enum=False),
        nullable=False,
        default=MeetingProvider.GOOGLE_MEET,
    )
    timezone: Mapped[MeetingTimezone] = mapped_column(
        Enum(MeetingTimezone, native_enum=False),
        nullable=False,
        default=MeetingTimezone.ASIA_YEKATERINBURG,
    )
    meeting_duration_minutes: Mapped[MeetingDurationMinutes] = mapped_column(
        Enum(MeetingDurationMinutes, native_enum=False),
        nullable=False,
        default=MeetingDurationMinutes.THIRTY,
    )
