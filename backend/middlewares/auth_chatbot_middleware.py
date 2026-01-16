from functools import wraps
from flask import request, jsonify
import jwt
from datetime import datetime, timedelta
import os
import secrets
from werkzeug.security import check_password_hash
from Models.user_details_model import UserDetails
from Models.user_role_model import UserRole
from Models.user_permission_mapping_model import UserPermissionMapping

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_IN_PROD")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "CHANGE_IN_PROD")
JWT_ALGORITHM = "HS256"

ACCESS_EXPIRES_MINUTES = 15
REFRESH_EXPIRES_DAYS = 7


def generate_access_token_chatbot(sender_id):
    payload = {
        "sender_id": sender_id,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRES_MINUTES),
        "iat": datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def generate_refresh_token_chatbot(sender_id):
    payload = {
        "sender_id": sender_id,
        "exp": datetime.utcnow() + timedelta(days=REFRESH_EXPIRES_DAYS),
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_hex(16)  # unique ID for token rotation
    }
    return jwt.encode(payload, REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM)



def verify_access_token_chatbot(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload if payload.get("type") == "access" else None
    except:
        return None


def verify_refresh_token_chatbot(token):
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload if payload.get("type") == "refresh" else None
    except:
        return None


def chatbot_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 1️⃣ ALWAYS check HttpOnly cookie first (your login uses cookies)    
        token = request.cookies.get("chatbot_access_token")

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

        # 4️⃣ Validate JWT
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired", "status": False}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid or expired token", "status": False}), 401

        # 5️⃣ Attach user info to request context
        request.sender_id = data.get("sender_id")

        return f(*args, **kwargs)
    return decorated


