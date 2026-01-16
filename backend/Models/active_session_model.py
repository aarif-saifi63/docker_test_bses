"""
SECURITY: Active Session Token Binding Model
Prevents token hijacking attacks by binding tokens to specific user sessions

This addresses the vulnerability where:
1. Attacker intercepts an admin's access token
2. Attacker logs in as a different user (developer)
3. Attacker uses intercepted admin token to gain unauthorized access

Solution:
- Each token is bound to a specific user_id and session
- Middleware validates that the token belongs to the authenticated user
- Tokens cannot be reused by different users
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from database import Base, SessionLocal
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)

class ActiveSession(Base):
    __tablename__ = "active_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    access_token_hash = Column(String(64), nullable=False, unique=True, index=True)
    refresh_token_hash = Column(String(64), nullable=True, index=True)
    session_id = Column(String(64), nullable=True, index=True)  # 🔒 SECURITY: Store SID for session fixation protection
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=current_time_ist)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=current_time_ist, onupdate=current_time_ist)

    # Composite index for fast lookups
    __table_args__ = (
        Index('idx_user_token', 'user_id', 'access_token_hash'),
        Index('idx_token_sid', 'access_token_hash', 'session_id'),  # 🔒 Index for SID validation
    )

    @staticmethod
    def create_session(user_id, access_token_hash, refresh_token_hash, expires_at, session_id=None, ip_address=None, user_agent=None):
        """
        SECURITY: Create a new active session binding

        Args:
            user_id: The user ID this token belongs to
            access_token_hash: SHA-256 hash of the access token
            refresh_token_hash: SHA-256 hash of the refresh token
            expires_at: Token expiration time
            session_id: Session ID (SID) for session fixation protection
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)
        """
        db = SessionLocal()
        try:
            session = ActiveSession(
                user_id=user_id,
                access_token_hash=access_token_hash,
                refresh_token_hash=refresh_token_hash,
                session_id=session_id,  # 🔒 Store SID
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session.id
        finally:
            db.close()

    @staticmethod
    def validate_token_ownership(user_id, access_token_hash):
        """
        SECURITY: Validate that the token belongs to the specified user

        This prevents token hijacking by ensuring:
        1. Token exists in active sessions
        2. Token is bound to the correct user_id
        3. Token has not expired

        Args:
            user_id: The user ID from the token payload
            access_token_hash: SHA-256 hash of the access token

        Returns:
            bool: True if token is valid and belongs to user, False otherwise
        """
        db = SessionLocal()
        try:
            session = db.query(ActiveSession).filter(
                ActiveSession.user_id == user_id,
                ActiveSession.access_token_hash == access_token_hash,
                ActiveSession.expires_at > current_time_ist()
            ).first()

            if session:
                # Update last activity
                session.last_activity = current_time_ist()
                db.commit()
                return True
            return False
        finally:
            db.close()

    @staticmethod
    def validate_token_with_session(user_id, access_token_hash, session_id):
        """
        SECURITY: Validate token ownership AND session fixation protection

        This is the CRITICAL security check that prevents token hijacking by:
        1. Validating token belongs to the user (token ownership)
        2. Validating token is bound to the correct session (session fixation protection)

        Attack Prevention:
        - If attacker steals admin token and uses it in their session:
          → Token hash matches (admin's token)
          → User ID matches (admin from token payload)
          → Session ID DOES NOT match (attacker's SID != admin's SID)
          → ATTACK BLOCKED!

        Args:
            user_id: The user ID from the token payload
            access_token_hash: SHA-256 hash of the access token
            session_id: Current session ID (SID) from request

        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        db = SessionLocal()
        try:
            session_record = db.query(ActiveSession).filter(
                ActiveSession.user_id == user_id,
                ActiveSession.access_token_hash == access_token_hash,
                ActiveSession.expires_at > current_time_ist()
            ).first()

            if not session_record:
                return False, "Token not found or expired. Please login again."

            # 🔒 CRITICAL: Validate Session ID matches
            if session_record.session_id != session_id:
                print(f"🚨 TOKEN HIJACKING DETECTED!")
                print(f"   User ID from token: {user_id}")
                print(f"   Token hash: {access_token_hash[:16]}...")
                print(f"   Expected SID (from token's session): {session_record.session_id[:16] if session_record.session_id else 'None'}...")
                print(f"   Actual SID (from current request): {session_id[:16] if session_id else 'None'}...")

                return False, "Session mismatch. Token is being used in unauthorized session. Possible hijacking attack."

            # Update last activity
            session_record.last_activity = current_time_ist()
            db.commit()

            return True, None
        finally:
            db.close()

    @staticmethod
    def invalidate_session(access_token_hash):
        """
        SECURITY: Invalidate a session (used during logout)

        Args:
            access_token_hash: SHA-256 hash of the access token
        """
        db = SessionLocal()
        try:
            session = db.query(ActiveSession).filter(
                ActiveSession.access_token_hash == access_token_hash
            ).first()

            if session:
                db.delete(session)
                db.commit()
                return True
            return False
        finally:
            db.close()

    @staticmethod
    def invalidate_all_user_sessions(user_id):
        """
        SECURITY: Invalidate all sessions for a user
        Useful for force logout on password change or security breach

        Args:
            user_id: The user ID
        """
        db = SessionLocal()
        try:
            db.query(ActiveSession).filter(
                ActiveSession.user_id == user_id
            ).delete()
            db.commit()
        finally:
            db.close()

    @staticmethod
    def update_token_on_refresh(old_access_hash, new_access_hash, new_refresh_hash, new_expires_at, new_session_id=None):
        """
        SECURITY: Update session when token is refreshed

        Args:
            old_access_hash: Old access token hash
            new_access_hash: New access token hash
            new_refresh_hash: New refresh token hash
            new_expires_at: New expiration time
            new_session_id: New Session ID (SID) for session fixation protection
        """
        db = SessionLocal()
        try:
            session = db.query(ActiveSession).filter(
                ActiveSession.access_token_hash == old_access_hash
            ).first()

            if session:
                session.access_token_hash = new_access_hash
                session.refresh_token_hash = new_refresh_hash
                session.expires_at = new_expires_at
                session.last_activity = current_time_ist()
                if new_session_id:
                    session.session_id = new_session_id  # 🔒 Update SID on refresh
                db.commit()
                return True
            return False
        finally:
            db.close()

    @staticmethod
    def cleanup_expired_sessions():
        """
        SECURITY: Remove expired sessions from database
        Should be called periodically via scheduled job
        """
        db = SessionLocal()
        try:
            deleted = db.query(ActiveSession).filter(
                ActiveSession.expires_at < current_time_ist()
            ).delete()
            db.commit()
            return deleted
        finally:
            db.close()

    @staticmethod
    def get_user_active_sessions(user_id):
        """
        Get all active sessions for a user
        Useful for showing "Active Sessions" in user dashboard

        Args:
            user_id: The user ID

        Returns:
            list: List of active session dictionaries
        """
        db = SessionLocal()
        try:
            sessions = db.query(ActiveSession).filter(
                ActiveSession.user_id == user_id,
                ActiveSession.expires_at > current_time_ist()
            ).order_by(ActiveSession.last_activity.desc()).all()

            return [{
                'id': s.id,
                'ip_address': s.ip_address,
                'user_agent': s.user_agent,
                'created_at': s.created_at.isoformat(),
                'last_activity': s.last_activity.isoformat()
            } for s in sessions]
        finally:
            db.close()
