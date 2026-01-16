from functools import wraps
from flask import redirect, request, jsonify
import jwt
from datetime import datetime, timedelta
import os
import secrets
from werkzeug.security import check_password_hash
from Models.user_details_model import UserDetails
from Models.user_role_model import UserRole
from Models.user_permission_mapping_model import UserPermissionMapping
from Models.token_blacklist_model import TokenBlacklist
from database import SessionLocal
from utils.jwt_encryption import encrypt_jwt_payload, decrypt_jwt_payload

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_IN_PROD")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "CHANGE_IN_PROD")
JWT_ALGORITHM = "HS256"

ACCESS_EXPIRES_MINUTES = 15
REFRESH_EXPIRES_DAYS = 7


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

        print("------- bbebbenjebnebnebnbe:", token)

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
            # return jsonify(status=False, message="Session expired. Please login again."), 403
            return redirect_or_json("Session expired. Please login again.", 403)

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

