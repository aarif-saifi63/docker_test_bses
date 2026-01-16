from datetime import datetime
import os
import jwt
import json
from Models.permission_matrix_model import PermissionMatrix
from flask import make_response, request, jsonify
from werkzeug.security import check_password_hash
from Models.ad_model import current_time_ist
from Models.user_details_model import UserDetails
from Models.user_permission_mapping_model import UserPermissionMapping
from Models.user_role_model import UserRole
from Models.token_blacklist_model import TokenBlacklist
from database import SessionLocal
from middlewares.auth_middleware import ACCESS_EXPIRES_MINUTES, REFRESH_EXPIRES_DAYS, generate_access_token, generate_refresh_token, verify_refresh_token
from cryptography.fernet import Fernet
import os
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from utils.rsa_encryption import decrypt_data

# Load .env file
load_dotenv()

# key = os.getenv("ENCRYPTION_KEY","b'y8aIT06DjNY5VtEUvAhIFd5EIG7DruRI14kw3XEYDX0='")
key=b'y8aIT06DjNY5VtEUvAhIFd5EIG7DruRI14kw3XEYDX0='
cipher = Fernet(key)


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_IN_PROD")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "CHANGE_IN_PROD")



# Register user
def register_user_detail():
    try:
        data = request.get_json()
        email_id = data.get("email_id")
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        role_id = data.get("role_id")
        name = data.get("name")

        if not email_id or not password or not role_id:
            return jsonify(status=False, message="Email, password, and role_id are required"), 400

        if password != confirm_password:
            return jsonify(status=False, message="Password and confirm password do not match"), 400

        db = SessionLocal()
        role = db.query(UserRole).filter_by(id=role_id).first()
        db.close()
        if not role:
            return jsonify(status=False, message="Invalid role_id"), 400
        
        # Encrypt email for storage
        encrypted_email = cipher.encrypt(email_id.encode()).decode()  # decode once to store as str

        # Check if user already exists
        existing_users = UserDetails.find_all()
        user_exists = False

        for u in existing_users:
            decrypted_email = u.email_id  # default: assume plain text
            try:
                decrypted_email = cipher.decrypt(u.email_id.encode()).decode()
            except Exception as e:
                print(f"Email {u.email_id} could not be decrypted, assuming plain: {e}")

            print(f"Checking user: Encrypted/Plain: {u.email_id} | Decrypted: {decrypted_email}")

            if decrypted_email.lower() == email_id.lower():
                user_exists = True
                break

        if user_exists:
            return jsonify(status=False, message="Email already exists"), 400

        # Hash password
        hashed_password = generate_password_hash(password)


        # Save user
        user = UserDetails(
            email_id=encrypted_email,  # string, no decode
            password=hashed_password,
            role_id=role_id,
            name=name
        )
        user_id = user.save()       
        return jsonify(status=True, message="User registered successfully", user_id=user_id), 201

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


# Login user

import redis

# redis_client = redis.Redis(host='localhost', port=6379, db=0)

redis_client = redis.Redis(host=os.getenv('REDIS_HOST'),port=os.getenv('REDIS_PORT'), db=0)


# PROGRESSIVE RATE LIMITING CONSTANTS
# Prevents brute force attacks with exponential backoff
ATTEMPT_THRESHOLDS = {
    3: 60,        # After 3 failed attempts: 1 minute lockout
    5: 300,       # After 5 failed attempts: 5 minutes lockout
    7: 900,       # After 7 failed attempts: 15 minutes lockout
    10: 3600,     # After 10 failed attempts: 1 hour lockout
    15: 86400,    # After 15 failed attempts: 24 hours lockout
}

def get_progressive_lockout_time(attempts):
    """
    SECURITY: Calculate progressive lockout time based on failed attempts
    Returns lockout duration in seconds
    """
    for threshold, lockout_seconds in sorted(ATTEMPT_THRESHOLDS.items(), reverse=True):
        if attempts >= threshold:
            return lockout_seconds
    return 0

def check_rate_limit(ip, email):
    """
    SECURITY: Progressive rate limiting for login attempts

    Tracks both IP-based and email-based attempts to prevent:
    - Brute force attacks from single IP
    - Distributed attacks on single account
    - Credential stuffing attacks

    Returns: (is_blocked, remaining_time, attempts)
    """
    ip_key = f"login_attempts:ip:{ip}"
    email_key = f"login_attempts:email:{email}" if email else None
    lockout_key = f"login_lockout:{ip}:{email}" if email else f"login_lockout:{ip}"

    # Check if currently locked out
    lockout_ttl = redis_client.ttl(lockout_key)
    if lockout_ttl > 0:
        return True, lockout_ttl, None

    # Get current attempt counts
    ip_attempts = redis_client.get(ip_key)
    ip_attempts = int(ip_attempts) if ip_attempts else 0

    email_attempts = 0
    if email_key:
        email_attempts = redis_client.get(email_key)
        email_attempts = int(email_attempts) if email_attempts else 0

    # Use the higher of IP or email attempts for progressive lockout
    max_attempts = max(ip_attempts, email_attempts)

    return False, 0, max_attempts

def record_failed_login(ip, email):
    """
    SECURITY: Record failed login attempt and apply progressive lockout

    Args:
        ip: Client IP address
        email: Login email attempt

    Returns:
        tuple: (lockout_duration, total_attempts)
    """
    ip_key = f"login_attempts:ip:{ip}"
    email_key = f"login_attempts:email:{email}" if email else None
    lockout_key = f"login_lockout:{ip}:{email}" if email else f"login_lockout:{ip}"

    pipe = redis_client.pipeline()

    # Increment IP attempts
    pipe.incr(ip_key)
    pipe.expire(ip_key, 86400)  # Track attempts for 24 hours

    # Increment email attempts if email provided
    if email_key:
        pipe.incr(email_key)
        pipe.expire(email_key, 86400)  # Track attempts for 24 hours

    results = pipe.execute()
    ip_attempts = results[0]
    email_attempts = results[2] if email_key else 0

    # Use the higher count for progressive lockout
    max_attempts = max(ip_attempts, email_attempts)

    # Calculate progressive lockout time
    lockout_duration = get_progressive_lockout_time(max_attempts)

    if lockout_duration > 0:
        # Set lockout
        redis_client.setex(lockout_key, lockout_duration, max_attempts)

    return lockout_duration, max_attempts

def clear_login_attempts(ip, email):
    """
    SECURITY: Clear login attempts after successful login
    """
    ip_key = f"login_attempts:ip:{ip}"
    email_key = f"login_attempts:email:{email}" if email else None
    lockout_key = f"login_lockout:{ip}:{email}" if email else f"login_lockout:{ip}"

    redis_client.delete(ip_key)
    if email_key:
        redis_client.delete(email_key)
    redis_client.delete(lockout_key)


def login_user_detail():
    try:
        ip = request.remote_addr
        data = request.get_json()

        # SECURITY: Check if payload is RSA-encrypted
        encrypted_payload = data.get("encrypted_payload")

        if encrypted_payload:
            # Decrypt RSA-encrypted payload
            try:
                decrypted_json = decrypt_data(encrypted_payload)
                decrypted_data = json.loads(decrypted_json)
                email_id = decrypted_data.get("email_id")
                password = decrypted_data.get("password")

                print(f"[RSA] Decrypted login payload for email: {email_id}")

            except ValueError as e:
                return jsonify({
                    "status": False,
                    "message": "Failed to decrypt login credentials. Invalid encryption."
                }), 400
            except json.JSONDecodeError:
                return jsonify({
                    "status": False,
                    "message": "Invalid encrypted payload format"
                }), 400
        else:
            # Fallback to plain credentials (backward compatibility)
            email_id = data.get("email_id")
            password = data.get("password")
            print(f"[PLAIN] Login attempt with plain credentials for email: {email_id}")

        if not email_id or not password:
            return jsonify({
                "status": False,
                "message": "Email and password are required"
            }), 400

        # SECURITY: Check progressive rate limit
        is_blocked, remaining_time, current_attempts = check_rate_limit(ip, email_id)

        if is_blocked:
            # Convert seconds to human-readable format
            if remaining_time >= 3600:
                time_str = f"{remaining_time // 3600} hour(s)"
            elif remaining_time >= 60:
                time_str = f"{remaining_time // 60} minute(s)"
            else:
                time_str = f"{remaining_time} second(s)"

            return jsonify({
                "status": False,
                "message": f"Account temporarily locked due to multiple failed login attempts. Try again after {time_str}.",
                "lockout_remaining": remaining_time
            }), 429

        print(f"-----------------------------Login attempt for email: {email_id}")
        print(f"-----------------------------From IP: {ip}")
        print(f"-----------------------------Current failed attempts: {current_attempts}")

        existing_users = UserDetails.find_all()
        user = False

        for u in existing_users:
            decrypted_email = u.email_id  # default: assume plain text
            try:
                decrypted_email = cipher.decrypt(u.email_id.encode()).decode()
            except Exception as e:
                print(f"Email {u.email_id} could not be decrypted, assuming plain: {e}")

            print(f"Checking user: Encrypted/Plain: {u.email_id} | Decrypted: {decrypted_email}")

            if decrypted_email.lower() == email_id.lower():
                user = u
                break


        # user = UserDetails.find_by_email(email_id)

        if not user:
            # SECURITY: Record failed login attempt
            lockout_duration, total_attempts = record_failed_login(ip, email_id)

            if lockout_duration > 0:
                if lockout_duration >= 3600:
                    time_str = f"{lockout_duration // 3600} hour(s)"
                elif lockout_duration >= 60:
                    time_str = f"{lockout_duration // 60} minute(s)"
                else:
                    time_str = f"{lockout_duration} second(s)"

                return jsonify({
                    "status": False,
                    "message": f"Invalid login credentials. Account locked for {time_str} after {total_attempts} failed attempts.",
                    "lockout_duration": lockout_duration
                }), 429

            # Return generic error (don't reveal if email exists)
            return jsonify(status=False, message="Invalid login credentials"), 400

        print("-----------------------------User fetched for login:", user)
        print(user.email_id, user.role_id, "-----------------------------Checking password hash:")

        if not check_password_hash(user.password, password):
            # SECURITY: Record failed login attempt
            lockout_duration, total_attempts = record_failed_login(ip, email_id)

            if lockout_duration > 0:
                if lockout_duration >= 3600:
                    time_str = f"{lockout_duration // 3600} hour(s)"
                elif lockout_duration >= 60:
                    time_str = f"{lockout_duration // 60} minute(s)"
                else:
                    time_str = f"{lockout_duration} second(s)"

                return jsonify({
                    "status": False,
                    "message": f"Invalid login credentials. Account locked for {time_str} after {total_attempts} failed attempts.",
                    "lockout_duration": lockout_duration
                }), 429

            # Return generic error
            return jsonify(status=False, message="Invalid login credentials"), 400

        # Fetch role info
        role = UserRole.find_by_id(user.role_id)
        role_name = role.role_name if role else "Unknown"

        # Fetch permissions
        role_permissions = UserPermissionMapping.get_permissions_by_role(user.role_id)
        user_permissions = UserPermissionMapping.get_permissions_for_user(
            user_details_id=user.id, 
            role_id=user.role_id
        )

        # Merge and remove duplicates
        merged_permissions = {
            (p['permission_name'], p['module'], p['crud_action']): p
            for p in role_permissions + user_permissions
        }
        unique_permissions = list(merged_permissions.values())

        # SECURITY: Clear failed login attempts on successful login
        clear_login_attempts(ip, email_id)

        # Generate tokens
        access_token = generate_access_token(str(user.id), user.email_id, user.role_id)
        refresh_token = generate_refresh_token(str(user.id), user.email_id, user.role_id)

        # Response payload
        user_details = {
            "id": str(user.id),
            "name": user.name,
            "email_id": email_id,
            "role_id": user.role_id,
            "role_name": role_name,
            "permissions": unique_permissions
        }

        # Create response
        response = make_response(jsonify({
            "status": True,
            "message": "Login successful",
            "data": {
                "user_details": user_details
            }
        }), 200)

        # SET HTTP-ONLY COOKIES (THIS WAS MISSING!)
        response.set_cookie(
            "access_token",
            access_token,
            httponly=True,
            max_age=ACCESS_EXPIRES_MINUTES * 60,
            secure=True,          # Local dev me false
            samesite="None",        # Local dev me Lax
            path="/"
        )

        response.set_cookie(
            'refresh_token',
            refresh_token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=7 * 24 * 60 * 60,  # 7 days (matches REFRESH_EXPIRES_DAYS)
            path='/'
        )

        # RETURN THE RESPONSE (THIS WAS ALSO MISSING!)
        return response

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify(status=False, message="Login failed"), 500 
    




# def login_user_detail():
#     try:

#         ip = request.remote_addr

#         # === IP RATE LIMIT CHECK ===
#         if is_ip_rate_limited(ip):
#             return jsonify({
#                 "status": False,
#                 "message": "Too many login attempts from your IP. Try again after 1 minute."
#             }), 429

#         data = request.get_json()
#         email_id = data.get("email_id")
#         password = data.get("password")

#         print("-----------------------------Login attempt for email:", email_id)
#         print("-----------------------------From IP:", password)

#         existing_users = UserDetails.find_all()
#         user = False

#         for u in existing_users:
#             decrypted_email = u.email_id  # default: assume plain text
#             try:
#                 decrypted_email = cipher.decrypt(u.email_id.encode()).decode()
#             except Exception as e:
#                 print(f"Email {u.email_id} could not be decrypted, assuming plain: {e}")

#             print(f"Checking user: Encrypted/Plain: {u.email_id} | Decrypted: {decrypted_email}")

#             if decrypted_email.lower() == email_id.lower():
#                 user = u
#                 break


#         # user = UserDetails.find_by_email(email_id)

#         if not user:
#             return jsonify(status=False, message="Invalid login credentials"), 400

#         print("-----------------------------User fetched for login:", user)
#         print(user.email_id, user.role_id, "-----------------------------Checking password hash:")

#         if not check_password_hash(user.password, password):
#             return jsonify(status=False, message="Invalid login credentials"), 400

#         # Fetch role info
#         role = UserRole.find_by_id(user.role_id)
#         role_name = role.role_name if role else "Unknown"

#         # Fetch permissions
#         role_permissions = UserPermissionMapping.get_permissions_by_role(user.role_id)
#         user_permissions = UserPermissionMapping.get_permissions_for_user(
#             user_details_id=user.id, 
#             role_id=user.role_id
#         )

#         # Merge and remove duplicates
#         merged_permissions = {
#             (p['permission_name'], p['module'], p['crud_action']): p
#             for p in role_permissions + user_permissions
#         }
#         unique_permissions = list(merged_permissions.values())

#         # Generate tokens
#         access_token = generate_access_token(str(user.id), user.email_id, user.role_id)
#         refresh_token = generate_refresh_token(str(user.id), user.email_id, user.role_id)

#         # Response payload
#         user_details = {
#             "id": str(user.id),
#             "name": user.name,
#             "email_id": email_id,
#             "role_id": user.role_id,
#             "role_name": role_name,
#             "permissions": unique_permissions
#         }

#         # Create response
#         response = make_response(jsonify({
#             "status": True,
#             "message": "Login successful",
#             "data": {
#                 "user_details": user_details
#             }
#         }), 200)

#         #  SET HTTP-ONLY COOKIES (THIS WAS MISSING!)
#         response.set_cookie(
#             "access_token",
#             access_token,
#             httponly=True,
#             max_age=ACCESS_EXPIRES_MINUTES * 60,
#             secure=True,          # Local dev me false
#             samesite="None",        # Local dev me Lax
#             path="/"
#         )

#         response.set_cookie(
#             'refresh_token',
#             refresh_token,
#             httponly=True,
#             secure=True,
#             samesite="None",
#             max_age=7 * 24 * 60 * 60,  # 7 days (matches REFRESH_EXPIRES_DAYS)
#             path='/'
#         )

#         # RETURN THE RESPONSE (THIS WAS ALSO MISSING!)
#         return response

#     except Exception as e:
#         print(f"Login error: {str(e)}")
#         return jsonify(status=False, message="Login failed"), 500 
    

def refresh_token():
    refresh_cookie = request.cookies.get("refresh_token")

    if not refresh_cookie:
        return jsonify({"status": False, "message": "Missing refresh token"}), 401

    payload = verify_refresh_token(refresh_cookie)
    if not payload:
        return jsonify({"status": False, "message": "Invalid or expired refresh token"}), 401

    # ROTATE refresh token (security best practice)
    new_access = generate_access_token(payload["user_id"], payload["email_id"], payload["role_id"])
    new_refresh = generate_refresh_token(payload["user_id"], payload["email_id"], payload["role_id"])

    response = jsonify({"status": True, "message": "Token refreshed"})

    response.set_cookie("access_token", new_access, httponly=True, secure=True, samesite="None", path="/")
    response.set_cookie("refresh_token", new_refresh, httponly=True, secure=True, samesite="None", path="/")

    return response

# Get all users
def get_all_users():
    try:
        db = SessionLocal()
        # Fetch users with their roles
        users = db.query(UserDetails, UserRole.role_name).join(UserRole, UserDetails.role_id == UserRole.id).all()

        user_list = []

        for user, role_name in users:
            # Fetch role-based permissions
            role_permissions = (
                db.query(PermissionMatrix.id, PermissionMatrix.permission_name, PermissionMatrix.module, PermissionMatrix.crud_action)
                .join(UserPermissionMapping, PermissionMatrix.id == UserPermissionMapping.permission_id)
                .filter(UserPermissionMapping.user_role_id == user.role_id)
                .all()
            )

            # Fetch user-specific permissions
            user_permissions = (
                db.query(PermissionMatrix.id, PermissionMatrix.permission_name, PermissionMatrix.module, PermissionMatrix.crud_action)
                .join(UserPermissionMapping, PermissionMatrix.id == UserPermissionMapping.permission_id)
                .filter(UserPermissionMapping.user_details_id == user.id)
                .all()
            )

            # Merge permissions with ID
            merged_permissions = { (p[0], p[1], p[2], p[3]): p for p in role_permissions + user_permissions }

            # Format arrays
            role_perm_list = [
                {"id": p[0], "permission_name": p[1], "module": p[2], "crud_action": p[3]} for p in role_permissions
            ]
            user_perm_list = [
                {"id": p[0], "permission_name": p[1], "module": p[2], "crud_action": p[3]} for p in user_permissions
            ]
            combined_perm_list = [
                {"id": p[0], "permission_name": p[1], "module": p[2], "crud_action": p[3]} for p in merged_permissions.values()
            ]

            decrypted_email = user.email_id  # default: assume plain text
            try:
                decrypted_email = cipher.decrypt(user.email_id.encode()).decode()
            except Exception as e:
                print(f"Email {user.email_id} could not be decrypted, assuming plain: {e}")

            user_list.append({
                "id": user.id,
                "name": user.name,
                "email_id": decrypted_email,
                "role_id": user.role_id,
                "role_name": role_name,
                "role_permissions": role_perm_list,
                "user_permissions": user_perm_list,
                "permissions": combined_perm_list
            })

        return jsonify(status=True, message="Users List with Permissions", data=user_list), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500
    finally:
        db.close()



def logout_user():
    """
    SECURITY: Logout user and blacklist encrypted tokens

    Decrypts tokens before blacklisting to ensure they are properly invalidated
    """
    from middlewares.auth_middleware import verify_access_token, verify_refresh_token
    from utils.jwt_encryption import decrypt_jwt_payload

    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    # BLACKLIST BOTH TOKENS
    try:
        db = SessionLocal()
        if access_token:
            try:
                # Decrypt the encrypted token to get payload
                data = verify_access_token(access_token)
                if data:
                    expiry = datetime.utcfromtimestamp(data["exp"])
                    # Store the encrypted token in blacklist
                    db.add(TokenBlacklist(token=access_token, expires_at=expiry))
            except Exception as e:
                print(f"Failed to blacklist access token: {str(e)}")
                pass  # ignore bad token

        if refresh_token:
            try:
                # Decrypt the encrypted token to get payload
                data = verify_refresh_token(refresh_token)
                if data:
                    expiry = datetime.utcfromtimestamp(data["exp"])
                    # Store the encrypted token in blacklist
                    db.add(TokenBlacklist(token=refresh_token, expires_at=expiry))
            except Exception as e:
                print(f"Failed to blacklist refresh token: {str(e)}")
                pass

        db.commit()

        # CLEAR COOKIES
        response = make_response(jsonify({
            "status": True,
            "message": "Logged out successfully"
        }), 200)

        response.set_cookie('access_token', '', max_age=0, httponly=True, secure=True, samesite="Strict", path='/')
        response.set_cookie('refresh_token', '', max_age=0, httponly=True, secure=True, samesite="Strict", path='/')

        return response
    finally:
        db.close()


def update_user(user_id):
    try:
        data = request.get_json()
        db = SessionLocal()

        # Fetch the user
        user = db.query(UserDetails).filter_by(id=user_id).first()
        if not user:
            return jsonify(status=False, message="User not found"), 404

        # Update allowed fields
        name = data.get("name")
        email_id = data.get("email_id")
        role_id = data.get("role_id")

        if email_id:
            # Check if email is already taken by another user
            existing = db.query(UserDetails).filter(UserDetails.email_id == email_id, UserDetails.id != user_id).first()
            if existing:
                return jsonify(status=False, message="Email already exists"), 400
            user.email_id = email_id

        if name:
            user.name = name

        if role_id:
            # Validate role_id exists
            role_exists = db.query(UserRole).filter_by(id=role_id).first()
            if not role_exists:
                return jsonify(status=False, message="Invalid role_id"), 400
            user.role_id = role_id

        user.updated_at = current_time_ist()
        db.commit()
        db.refresh(user)

        updated_user = {
            "id": user.id,
            "name": user.name,
            "email_id": user.email_id,
            "role_id": user.role_id
        }

        return jsonify(status=True, message="User updated successfully", data=updated_user), 200

    except Exception as e:
        db.rollback()
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500
    finally:
        db.close()



# def get_user_permission(user_id):
#     try:
#         # data = request.get_json()

#         # Fetch user
#         user = UserDetails.find_one(id=user_id)
#         if not user:
#             return jsonify(status=False, message="User not found"), 404

#         # Fetch role info
#         role = UserRole.find_by_id(user.role_id)
#         role_name = role.role_name if role else "Unknown"

#         # Fetch permissions
#         role_permissions = UserPermissionMapping.get_permissions_by_role(user.role_id)
#         user_permissions = UserPermissionMapping.get_permissions_for_user(user_details_id=user.id, role_id=user.role_id)

#         # Merge and remove duplicates
#         merged_permissions = { 
#             (p['permission_name'], p['module'], p['crud_action']): p 
#             for p in role_permissions + user_permissions
#         }
#         unique_permissions = list(merged_permissions.values())

#         # Response payload
#         user_details = {
#             "id": str(user.id),
#             "name": user.name,
#             "email_id": user.email_id,
#             "role_id": user.role_id,
#             "role_name": role_name,
#             "permissions": unique_permissions
#         }

#         return jsonify(
#             status=True,
#             message="Login successful",
#             data={"user_details": user_details}
#         ), 200

#     except Exception as e:
#         return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


def get_user_permission():
    try:
        # Get user_id from token (set by token_required)
        user_id = request.user_id

        print("-----------------------------Fetching permissions for user_id:", user_id)

        # Fetch user
        user = UserDetails.find_one(id=user_id)
        if not user:
            return jsonify(status=False, message="User not found"), 404

        # Fetch role info
        role = UserRole.find_by_id(user.role_id)
        role_name = role.role_name if role else "Unknown"

        # Fetch permissions
        role_permissions = UserPermissionMapping.get_permissions_by_role(user.role_id)
        user_permissions = UserPermissionMapping.get_permissions_for_user(
            user_details_id=user.id,
            role_id=user.role_id
        )

        # Merge & remove duplicates
        merged_permissions = {
            (p['permission_name'], p['module'], p['crud_action']): p
            for p in (role_permissions + user_permissions)
        }
        unique_permissions = list(merged_permissions.values())

        # Prepare response
        user_details = {
            "id": str(user.id),
            "name": user.name,
            "email_id": user.email_id,
            "role_id": user.role_id,
            "role_name": role_name,
            "permissions": unique_permissions
        }

        return jsonify(
            status=True,
            message="User permissions fetched successfully",
            data={"user_details": user_details}
        ), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500
    

def delete_user(user_id):
    db = SessionLocal()
    try:
        # Delete all related permission mappings first
        db.query(UserPermissionMapping).filter_by(user_details_id=user_id).delete()

        # Fetch user
        user = db.query(UserDetails).filter_by(id=user_id).first()
        if not user:
            return jsonify(status=False, message="User not found"), 404

        # Delete user
        db.delete(user)
        db.commit()

        return jsonify(status=True, message="User deleted successfully"), 200

    except Exception as e:
        db.rollback()
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500

    finally:
        db.close()
