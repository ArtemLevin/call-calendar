"""merge colleagues branch head

Revision ID: 6825f92b253a
Revises: a7d3c9e4b112, c2a7f8d9e210
Create Date: 2026-05-26 12:17:29.417503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6825f92b253a'
down_revision: Union[str, Sequence[str], None] = ('a7d3c9e4b112', 'c2a7f8d9e210')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
