"""add to model User is_verified field

Revision ID: 4b9edf2fb8de
Revises: d12801d15d8d
Create Date: 2025-01-31 10:12:38.325222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b9edf2fb8de'
down_revision: Union[str, None] = 'd12801d15d8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'is_verified')
    # ### end Alembic commands ###
