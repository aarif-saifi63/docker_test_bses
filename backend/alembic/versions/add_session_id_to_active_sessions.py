"""Add session_id column to active_sessions for session fixation protection

Revision ID: session_fixation_001
Revises: active_sessions_001
Create Date: 2026-01-08 00:00:00.000000

SECURITY: This migration adds session_id column to the active_sessions table
to prevent session fixation and token hijacking attacks.

The session_id (SID) binds each token to its specific session context, ensuring
that even if an attacker steals an admin's token, they cannot use it in their
own session because the SID validation will fail.

Attack Prevention:
- Admin logs in → token_admin + SID_admin stored in DB
- Attacker steals token_admin
- Attacker tries to use it in their session with SID_attacker
- Validation fails: token's SID (SID_admin) != request SID (SID_attacker)
- Attack BLOCKED!
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'session_fixation_001'
# MERGE: This migration merges two branches:
# 1. active_sessions_001 (active_sessions table creation)
# 2. ecd2b8657371 (otp_verified column addition)
down_revision: Union[str, Sequence[str], None] = ('active_sessions_001', 'ecd2b8657371')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    SECURITY: Add session_id column to active_sessions table

    This enables session fixation protection by binding tokens to specific
    session contexts. The session_id is a UUID that must match between:
    1. The database record (stored when token is created)
    2. The request cookie (sent by client)

    If they don't match, it indicates token hijacking attack.
    """
    # Add session_id column
    op.add_column(
        'active_sessions',
        sa.Column('session_id', sa.String(64), nullable=True, index=True)
    )

    # Create index on session_id for fast lookups
    op.create_index(
        'idx_session_id',
        'active_sessions',
        ['session_id']
    )

    # Create composite index on access_token_hash and session_id
    # This optimizes the critical security check: validate_token_with_session()
    op.create_index(
        'idx_token_sid',
        'active_sessions',
        ['access_token_hash', 'session_id']
    )

    print("✅ Session fixation protection migration completed!")
    print("✅ session_id column added to active_sessions table")
    print("✅ Indexes created for optimal security validation performance")


def downgrade() -> None:
    """
    Remove session fixation protection

    WARNING: Downgrading this migration will remove session fixation protection
    and make your API vulnerable to token hijacking attacks!
    """
    # Drop indexes first
    op.drop_index('idx_token_sid', table_name='active_sessions')
    op.drop_index('idx_session_id', table_name='active_sessions')

    # Drop session_id column
    op.drop_column('active_sessions', 'session_id')

    print("⚠️  WARNING: Session fixation protection has been removed!")
    print("⚠️  Your API is now vulnerable to token hijacking attacks!")
