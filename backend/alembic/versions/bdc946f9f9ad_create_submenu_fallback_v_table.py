"""create_submenu_fallback_v_table

Revision ID: bdc946f9f9ad
Revises: submenu_fallback_002
Create Date: 2026-01-19 16:31:28.800828

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision: str = 'bdc946f9f9ad'
down_revision: Union[str, Sequence[str], None] = 'submenu_fallback_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create submenu_fallback_v table."""
    op.create_table(
        'submenu_fallback_v',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('intent_names', sa.Text(), nullable=False),
        sa.Column('initial_msg', sa.Text(), nullable=False),
        sa.Column('final_msg', sa.Text(), nullable=False),
        sa.Column('user_type', ARRAY(sa.String()), nullable=True),
        sa.Column('language', sa.String(50), nullable=True),
        sa.UniqueConstraint('category', name='uq_submenu_fallback_v_category')
    )


def downgrade() -> None:
    """Drop submenu_fallback_v table."""
    op.drop_table('submenu_fallback_v')
