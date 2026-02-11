"""add new tier enum values

Revision ID: d4e5f6a7b8c9
Revises: c3f8a2d1e5b7
Create Date: 2026-02-11

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3f8a2d1e5b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new values to employmenttype enum
    op.execute("ALTER TYPE employmenttype ADD VALUE IF NOT EXISTS 'first_tier_proper'")
    op.execute("ALTER TYPE employmenttype ADD VALUE IF NOT EXISTS 'first_tier_freelancer'")
    # Add new value to subcontractingtierlimit enum
    op.execute("ALTER TYPE subcontractingtierlimit ADD VALUE IF NOT EXISTS 'second_tier'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # To downgrade, you would need to recreate the enum types without these values.
    pass
