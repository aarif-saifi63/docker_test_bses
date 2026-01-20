"""Add user_type and language columns to submenu_fallback_v table

Revision ID: submenu_fallback_002
Revises: session_fixation_001
Create Date: 2026-01-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision: str = 'submenu_fallback_002'
down_revision: Union[str, Sequence[str], None] = 'session_fixation_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add user_type (array) and language columns to submenu_fallback_v table.

    - user_type: Array of strings to support multiple user types (e.g., ['new_consumer', 'registered_consumer'])
    - language: String column to specify the language of the fallback message
    """
    # Check if table exists before modifying
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'submenu_fallback_v' in tables:
        # Check existing columns
        columns = [c['name'] for c in inspector.get_columns('submenu_fallback_v')]

        # Add user_type column (array of strings)
        if 'user_type' not in columns:
            op.add_column(
                'submenu_fallback_v',
                sa.Column('user_type', ARRAY(sa.String()), nullable=True)
            )
            print("✅ Added user_type column to submenu_fallback_v table")
        else:
            print("ℹ️  user_type column already exists in submenu_fallback_v table")

        # Add language column (string)
        if 'language' not in columns:
            op.add_column(
                'submenu_fallback_v',
                sa.Column('language', sa.String(50), nullable=True)
            )
            print("✅ Added language column to submenu_fallback_v table")
        else:
            print("ℹ️  language column already exists in submenu_fallback_v table")
    else:
        print("⚠️  Warning: submenu_fallback_v table does not exist")


def downgrade() -> None:
    """
    Remove user_type and language columns from submenu_fallback_v table.
    """
    # Drop the columns in reverse order
    op.drop_column('submenu_fallback_v', 'language')
    op.drop_column('submenu_fallback_v', 'user_type')

    print("⚠️  Removed user_type and language columns from submenu_fallback_v table")
