"""Model package exports.

Why: importing concrete models here allows migration tooling to load this
package once and receive complete metadata, preventing empty autogenerates.
"""

from app.db.models.booking import Booking

__all__ = ["Booking"]
