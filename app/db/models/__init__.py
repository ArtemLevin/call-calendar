"""Model package exports.

Why: importing concrete models here allows migration tooling to load this
package once and receive complete metadata, preventing empty autogenerates.
"""

from app.db.models.booking import Booking
from app.db.models.colleague import Colleague
from app.db.models.meeting_settings import MeetingSettings

__all__ = ["Booking", "MeetingSettings", "Colleague"]
