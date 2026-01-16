from functools import wraps
from flask import redirect, request, jsonify, session, make_response
import jwt
from datetime import datetime, timedelta
import os
import secrets
import hashlib
import uuid
from werkzeug.security import check_password_hash
from Models.user_details_model import UserDetails
from Models.user_role_model import UserRole
from Models.user_permission_mapping_model import UserPermissionMapping
from Models.token_blacklist_model import TokenBlacklist
from Models.active_session_model import ActiveSession
from database import SessionLocal
from utils.jwt_encryption import encrypt_jwt_payload, decrypt_jwt_payload

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_IN_PROD")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "CHANGE_IN_PROD")
JWT_ALGORITHM = "HS256"

ACCESS_EXPIRES_MINUTES = 15
REFRESH_EXPIRES_DAYS = 7


# ==========================================
# SESSION FIXATION PROTECTION FUNCTIONS
# ==========================================

def generate_session_id():
    """
    SECURITY: Generate a unique Session ID (SID) for session fixation protection

    This prevents session hijacking attacks where an attacker tries to use
    a stolen token in a different session context.

    Returns:
        str: A unique UUID-based session identifier
    """
    return str(uuid.uuid4())



def set_session_id(response, sid):
    """
    SECURITY: Set Session ID in server-side session ONLY (NOT as cookie)

    CRITICAL PROTECTION: SID is stored server-side only to prevent token hijacking!

    Why this prevents attacks:
    - Attacker steals access_token cookie → They have the token
    - Attacker tries to use it → Server checks SID
    - SID is in server session (not cookie) → Attacker doesn't have it
    - Attacker's SID (from their session) != Token's SID (from DB)
    - Attack BLOCKED!

    Args:
        response: Flask response object
        sid: Session ID to set

    Returns:
        response: Unmodified response (SID stored server-side only)
    """
    # Store SID in Flask server-side session ONLY
    # The SID NEVER leaves the server - cannot be intercepted!
    session['SID'] = sid
    session.permanent = True  # Make session persistent

    # 🔒 SECURITY: We deliberately DO NOT send SID as a cookie!
    # The SID exists only in server storage (Redis/filesystem)
    # Client only gets encrypted flask_session cookie
    # Even if attacker intercepts access_token, they cannot get the SID

    return response


def get_session_id():
    """
    SECURITY: Get Session ID from server-side session

    The SID is stored server-side only and never sent to the client.
    This prevents attackers from copying the SID even if they intercept all cookies.

    Returns:
        str or None: Session ID if exists, None otherwise
    """
    return session.get('SID')


def clear_session_data(response):
    """
    SECURITY: Clear all session data on logout

    Args:
        response: Flask response object

    Returns:
        response: Modified response with cleared session
    """
    # Clear server-side session (this clears the SID)
    session.clear()

    # No need to clear SID cookie since we never set it!
    # The SID only exists in server-side session storage

    return response


def hash_token(token):
    """
    SECURITY: Create SHA-256 hash of token for database storage
    We don't store raw tokens in database, only hashes

    Args:
        token: The JWT token string

    Returns:
        str: SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_access_token(user_id, email_id, role_id):
    """
    SECURITY: Generates an encrypted access token using JWE

    The token payload is first signed as JWT, then encrypted to prevent
    inspection and protect sensitive claims from being decoded.
    """
    payload = {
        "user_id": user_id,
        "email_id": email_id,
        "role_id": role_id,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRES_MINUTES),
        "iat": datetime.utcnow(),
        "type": "access"
    }
    # First, create standard JWT
    jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

    # Then, encrypt the entire JWT to prevent payload inspection
    encrypted_token = encrypt_jwt_payload(jwt_token)

    return encrypted_token


def generate_refresh_token(user_id, email_id, role_id):
    """
    SECURITY: Generates an encrypted refresh token using JWE

    The token payload is first signed as JWT, then encrypted to prevent
    inspection and protect sensitive claims from being decoded.
    """
    payload = {
        "user_id": user_id,
        "email_id": email_id,
        "role_id": role_id,
        "exp": datetime.utcnow() + timedelta(days=REFRESH_EXPIRES_DAYS),
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_hex(16)  # unique ID for token rotation
    }
    # First, create standard JWT
    jwt_token = jwt.encode(payload, REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM)

    # Then, encrypt the entire JWT to prevent payload inspection
    encrypted_token = encrypt_jwt_payload(jwt_token)

    return encrypted_token



def verify_access_token(encrypted_token):
    """
    SECURITY: Verifies and decrypts an encrypted access token

    Args:
        encrypted_token: The encrypted token from client

    Returns:
        dict: Decoded payload if valid, None otherwise
    """
    try:
        # First, decrypt the token to get the original JWT
        jwt_token = decrypt_jwt_payload(encrypted_token)

        # Then, verify and decode the JWT
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

        return payload if payload.get("type") == "access" else None
    except Exception as e:
        print(f"Token verification failed: {str(e)}")
        return None


def verify_refresh_token(encrypted_token):
    """
    SECURITY: Verifies and decrypts an encrypted refresh token

    Args:
        encrypted_token: The encrypted token from client

    Returns:
        dict: Decoded payload if valid, None otherwise
    """
    try:
        # First, decrypt the token to get the original JWT
        jwt_token = decrypt_jwt_payload(encrypted_token)

        # Then, verify and decode the JWT
        payload = jwt.decode(jwt_token, REFRESH_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        return payload if payload.get("type") == "refresh" else None
    except Exception as e:
        print(f"Refresh token verification failed: {str(e)}")
        return None
    
# def is_blacklisted(token):
#     return TokenBlacklist.query.filter_by(token=token).first() is not None
def is_blacklisted(token):
    db = SessionLocal()
    try:
        result = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
        return result is not None
    finally:
        db.close()


def redirect_or_json(message="Session expired", code=401):
    # Browser request --> redirect to login page
    if "text/html" in request.headers.get("Accept", ""):
        return redirect("/login")
    
    # API request (JSON)
    return jsonify({"status": False, "message": message}), code


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 1️⃣ ALWAYS check HttpOnly cookie first (your login uses cookies)
        token = request.cookies.get("access_token")

        print("------- Token from cookie:", token)

        # 2️⃣ If not found in cookie, fallback to Authorization header (optional)
        if not token:
            auth = request.headers.get("Authorization")
            if auth and auth.startswith("Bearer "):
                token = auth.split(" ")[1]

        # 3️⃣ Still no token → unauthorized
        if not token:
            return jsonify({
                "message": "Missing auth token",
                "status": False
            }), 401

        if is_blacklisted(token):
            return redirect_or_json("Unauthorized action", 403)

        # 4️⃣ Validate encrypted JWT
        try:
            # Decrypt and verify the token
            data = verify_access_token(token)
            if not data:
                return jsonify({"message": "Invalid or expired token", "status": False}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired", "status": False}), 401
        except Exception as e:
            print(f"Token validation error: {str(e)}")
            return jsonify({"message": "Invalid or expired token", "status": False}), 401

        # 🔒 CRITICAL SECURITY: Validate token ownership AND session fixation protection
        # This is the MAIN defense against token hijacking attacks
        user_id_from_token = data.get("user_id")
        token_hash = hash_token(token)

        # 🔒 CRITICAL SECURITY: Get SID from server-side session (NOT from cookie!)
        # This prevents token hijacking even if attacker intercepts access_token
        # because they cannot copy the SID (it's server-side only)
        current_sid = get_session_id()

        if not current_sid:
            print(f"🚨 SECURITY ALERT: No SID in server session!")
            print(f"   Token claims user_id: {user_id_from_token}")
            print(f"   IP: {request.remote_addr}")
            print(f"   This could be:")
            print(f"   - User not logged in (session expired)")
            print(f"   - Attacker using stolen token in different session")
            return jsonify({
                "message": "No active session found. Please login again.",
                "status": False
            }), 401

        # Validate token ownership AND session binding
        is_valid, error_msg = ActiveSession.validate_token_with_session(
            user_id_from_token,
            token_hash,
            current_sid
        )

        if not is_valid:
            print(f"🚨 SECURITY ALERT: Token hijacking attempt detected!")
            print(f"   Token claims user_id: {user_id_from_token}")
            print(f"   Token hash: {token_hash[:16]}...")
            print(f"   Current SID: {current_sid[:16]}...")
            print(f"   IP: {request.remote_addr}")
            print(f"   User-Agent: {request.headers.get('User-Agent', 'Unknown')}")

            # Clear potentially compromised session
            response = make_response(jsonify({
                "message": error_msg,
                "status": False,
                "error_code": "TOKEN_HIJACKING_DETECTED"
            }), 401)
            response = clear_session_data(response)
            return response

        # 5️⃣ Attach user info to request context
        request.user_id = data.get("user_id")
        request.email_id = data.get("email_id")
        request.role_id = data.get("role_id")

        return f(*args, **kwargs)
    return decorated





# def permission_required(module_name, crud_action):
#     """
#     Decorator to check if user has specific permission
#     Usage: @permission_required(module_name="Users", crud_action="create")

#     Args:
#         module_name: Name of the module (e.g., "Users", "Polls", "Ads")
#         crud_action: CRUD action (e.g., "create", "read", "update", "delete")

#     This decorator must be used after @token_required decorator
#     """
#     def decorator(f):
#         @wraps(f)
#         def decorated(*args, **kwargs):
#             # Check if user info is available (from token_required decorator)
#             if not hasattr(request, 'user_id') or not hasattr(request, 'role_id'):
#                 return jsonify({
#                     "status": False,
#                     "message": "User authentication information not found"
#                 }), 401

#             user_id = request.user_id
#             role_id = request.role_id

#             # Fetch user permissions
#             role_permissions = UserPermissionMapping.get_permissions_by_role(role_id)
#             user_permissions = UserPermissionMapping.get_permissions_for_user(
#                 user_details_id=user_id,
#                 role_id=role_id
#             )

#             # Merge permissions
#             all_permissions = role_permissions + user_permissions

#             # Check if user has the required permission
#             has_permission = any(
#                 p.get("module") == module_name and p.get("crud_action") == crud_action
#                 for p in all_permissions
#             )

#             print("-----------------------------User Permissions:", all_permissions, has_permission)

#             if not has_permission:
#                 return jsonify({
#                     "status": False,
#                     "message": f"Access denied. Required permission: {module_name} - {crud_action}"
#                 }), 403

#             return f(*args, **kwargs)

#         return decorated
#     return decorator

def permission_required(module_name, crud_action):
    """
    Checks user permissions.
    Must be used AFTER @token_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):

            # Ensure that authentication has run first
            if not hasattr(request, 'user_id') or not hasattr(request, 'role_id'):
                return jsonify({
                    "status": False,
                    "message": "Authentication required (user info missing)"
                }), 401

            user_id = request.user_id
            role_id = request.role_id

            # Fetch permissions from role + user-specific overrides
            role_permissions = UserPermissionMapping.get_permissions_by_role(role_id)
            user_permissions = UserPermissionMapping.get_permissions_for_user(
                user_details_id=user_id,
                role_id=role_id
            )

            # Combine permissions
            all_permissions = role_permissions + user_permissions

            # Check required permission
            has_permission = any(
                p.get("module") == module_name and p.get("crud_action") == crud_action
                for p in all_permissions
            )

            print("---- Permission Check ----")
            print("User:", user_id, "Role:", role_id)
            print("Permissions:", all_permissions)
            print("Required:", module_name, crud_action, "Allowed:", has_permission)

            if not has_permission:
                return jsonify({
                    "status": False,
                    "message": f"Access denied. Required permission: {module_name} - {crud_action}"
                }), 403

            return f(*args, **kwargs)

        return decorated
    return decorator



def optional_token():
    """
    Decorator for endpoints that can work with or without authentication.
    If token exists and is valid → user info added.
    If missing/invalid → continue without user info.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None

            # 1️⃣ First: check HttpOnly cookie (same as token_required)
            token = request.cookies.get("access_token")

            # 2️⃣ Fallback: Authorization header
            if not token:
                auth = request.headers.get("Authorization")
                if auth and auth.startswith("Bearer "):
                    token = auth.split(" ")[1]

            # Default: clear values so no leftover values exist
            request.user_id = None
            request.email_id = None
            request.role_id = None

            # 3️⃣ If token exists → try to decrypt and decode it
            if token:
                try:
                    # Decrypt and verify the token
                    data = verify_access_token(token)

                    if data:
                        # Set user on request context ONLY if valid
                        request.user_id = data.get("user_id")
                        request.email_id = data.get("email_id")
                        request.role_id = data.get("role_id")

                except Exception:
                    # Token invalid → ignore and continue without user
                    pass

            # 4️⃣ Continue normally regardless of token
            return f(*args, **kwargs)

        return decorated
    return decorator




def flexible_token_required(f):
    """
    Decorator that accepts EITHER admin token OR chatbot token
    Useful for endpoints that serve both admin and chatbot users
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Try admin token first (access_token cookie or Bearer)
        admin_token = request.cookies.get("access_token")
        if not admin_token:
            auth = request.headers.get("Authorization")
            if auth and auth.startswith("Bearer "):
                admin_token = auth.split(" ")[1]
        
        # Try chatbot token (chatbot_access_token cookie)
        chatbot_token = request.cookies.get("chatbot_access_token")
        
        # Validate admin token
        if admin_token:
            try:
                data = verify_access_token(admin_token)
                if data:
                    request.user_id = data.get("user_id")
                    request.email_id = data.get("email_id")
                    request.role_id = data.get("role_id")
                    request.auth_type = "admin"
                    return f(*args, **kwargs)
            except Exception as e:
                print(f"Admin token validation failed: {str(e)}")
        
        # Validate chatbot token
        if chatbot_token:
            try:
                data = jwt.decode(chatbot_token, SECRET_KEY, algorithms=["HS256"])
                if data.get("type") == "access":
                    request.sender_id = data.get("sender_id")
                    request.auth_type = "chatbot"
                    return f(*args, **kwargs)
            except Exception as e:
                print(f"Chatbot token validation failed: {str(e)}")
        
        # No valid token found
        return jsonify({
            "message": "Authentication required. Please login.",
            "status": False
        }), 401
    
    return decorated

