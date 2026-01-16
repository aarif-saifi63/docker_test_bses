"""Add active_sessions table for token-session binding security

Revision ID: active_sessions_001
Revises: 09f6d4b45a45
Create Date: 2025-01-07 00:00:00.000000

SECURITY: This migration adds the active_sessions table to prevent token hijacking attacks.
Each token is now bound to a specific user_id and validated on every request.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, DateTime, Text, Index


# revision identifiers, used by Alembic.
revision: str = 'active_sessions_001'
down_revision: Union[str, Sequence[str], None] = '09f6d4b45a45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    SECURITY: Create active_sessions table

    This table binds tokens to specific user sessions, preventing:
    1. Token hijacking attacks where attacker uses stolen admin token
    2. Cross-user token reuse
    3. Unauthorized privilege escalation
    """
    op.create_table(
        'active_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('access_token_hash', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('refresh_token_hash', sa.String(64), nullable=True, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True),  # Support IPv6
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
    )

    # Create composite index for fast lookups
    op.create_index(
        'idx_user_token',
        'active_sessions',
        ['user_id', 'access_token_hash']
    )


def downgrade() -> None:
    """Remove active_sessions table"""
    op.drop_index('idx_user_token', table_name='active_sessions')
    op.drop_table('active_sessions')
