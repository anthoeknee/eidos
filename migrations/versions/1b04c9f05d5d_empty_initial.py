"""empty_initial

Revision ID: 1b04c9f05d5d
Revises: 5af010037d9c
Create Date: 2025-01-04 06:09:09.096806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b04c9f05d5d'
down_revision: Union[str, None] = '5af010037d9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
