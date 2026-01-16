"""
One-Time Token Verification System

Prevents account takeover by replay attacks:
1. Login returns a one-time verification token
2. Client must verify with this token within 30 seconds
3. Token is immediately invalidated after verification
4. Without verification, the session is invalid

This prevents attackers from replaying captured login responses.
"""
import secrets
import redis
import os
from datetime import datetime

# Redis client for token storage
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=1  # Use different DB than rate limiting
)

# Token expiry in seconds (30 seconds - short window)
VERIFICATION_TOKEN_EXPIRY = 30


def generate_verification_token(user_id: str) -> str:
    """
    Generate a one-time verification token for post-login verification

    Args:
        user_id: The user ID to associate with this token

    Returns:
        str: A secure random verification token
    """
    # Generate a cryptographically secure random token
    verification_token = secrets.token_urlsafe(32)

    # Store in Redis with user_id as value and short expiry
    key = f"verify_token:{verification_token}"
    redis_client.setex(key, VERIFICATION_TOKEN_EXPIRY, user_id)

    print(f"[SECURITY] Generated verification token for user {user_id}, expires in {VERIFICATION_TOKEN_EXPIRY}s")

    return verification_token


def verify_and_consume_token(verification_token: str, expected_user_id: str) -> bool:
    """
    Verify a one-time token and immediately consume it

    Args:
        verification_token: The token to verify
        expected_user_id: The user ID that should match

    Returns:
        bool: True if valid and matches, False otherwise
    """
    key = f"verify_token:{verification_token}"

    # Get the stored user_id
    stored_user_id = redis_client.get(key)

    if not stored_user_id:
        print(f"[SECURITY] Verification token not found or expired: {verification_token[:10]}...")
        return False

    # Decode from bytes
    stored_user_id = stored_user_id.decode()

    # Verify user_id matches
    if stored_user_id != expected_user_id:
        print(f"[SECURITY] User ID mismatch for token. Expected: {expected_user_id}, Got: {stored_user_id}")
        return False

    # IMMEDIATELY DELETE the token (one-time use)
    redis_client.delete(key)

    print(f"[SECURITY] Verification token consumed successfully for user {expected_user_id}")

    return True


def invalidate_user_verification_tokens(user_id: str):
    """
    Invalidate all verification tokens for a specific user

    Args:
        user_id: The user ID whose tokens should be invalidated
    """
    # Scan for all tokens belonging to this user
    for key in redis_client.scan_iter(match="verify_token:*"):
        stored_user_id = redis_client.get(key)
        if stored_user_id and stored_user_id.decode() == user_id:
            redis_client.delete(key)
            print(f"[SECURITY] Invalidated verification token for user {user_id}")


def cleanup_expired_tokens():
    """
    Cleanup utility - Redis handles expiry automatically, but this can be used for manual cleanup
    """
    count = 0
    for key in redis_client.scan_iter(match="verify_token:*"):
        ttl = redis_client.ttl(key)
        if ttl == -2:  # Key doesn't exist
            redis_client.delete(key)
            count += 1

    if count > 0:
        print(f"[SECURITY] Cleaned up {count} expired verification tokens")

    return count
