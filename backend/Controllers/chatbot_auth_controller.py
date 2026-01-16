"""
Chatbot Authentication Controller

SECURITY: Secure authentication for chatbot frontend
- Generates JWT tokens for chatbot sessions
- Validates sender_id and creates secure sessions
- Implements token refresh mechanism
"""

import uuid
import logging
from flask import request, jsonify, make_response
from datetime import datetime
from middlewares.auth_chatbot_middleware import (
    generate_access_token_chatbot,
    generate_refresh_token_chatbot,
    verify_refresh_token_chatbot,
    ACCESS_EXPIRES_MINUTES,
    REFRESH_EXPIRES_DAYS
)
from Models.session_model import Session
from database import SessionLocal

# Configure logger
logging.basicConfig(
    filename='error.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)


def chatbot_init_session():
    """
    SECURITY: Initialize chatbot session with secure token generation

    Purpose:
    - Creates a new chatbot session with a server-generated sender_id
    - Returns access token (15 min) and refresh token (30 days)
    - Tokens are set as HttpOnly cookies for XSS protection

    Request Body (optional):
    {
        "user_agent": "Mozilla/5.0...",
        "ip_address": "192.168.1.1",
        "metadata": {
            "platform": "web",
            "version": "1.0"
        }
    }

    Response:
    {
        "status": true,
        "message": "Session initialized successfully",
        "data": {
            "sender_id": "uuid-here",
            "access_token": "jwt-token",
            "refresh_token": "jwt-token",
            "expires_in": 900  // seconds
        }
    }
    """
    try:
        # SECURITY: Generate secure random sender_id on server side
        sender_id = str(uuid.uuid4())

        # Get optional metadata from request
        data = request.get_json(silent=True) or {}
        user_agent = data.get("user_agent") or request.headers.get("User-Agent")
        ip_address = data.get("ip_address") or request.remote_addr
        metadata = data.get("metadata", {})

        # Create session in database
        # db = SessionLocal()
        # try:
        #     session = Session(
        #         user_id=sender_id,
        #         user_type="new",  # Default type for new sessions
        #         created_at=datetime.utcnow()
        #     )
        #     db.add(session)
        #     db.commit()

        #     logging.info(f"New chatbot session created: {sender_id}")
        # except Exception as e:
        #     db.rollback()
        #     logging.error(f"Failed to create session in DB: {str(e)}")
        #     # Continue anyway - session will be created on first interaction
        # finally:
        #     db.close()

        # Generate tokens
        access_token = generate_access_token_chatbot(sender_id)
        refresh_token = generate_refresh_token_chatbot(sender_id)

        # SECURITY: Set tokens as HttpOnly cookies to prevent XSS
        response = make_response(jsonify({
            "status": True,
            "message": "Session initialized successfully",
            "data": {
                "sender_id": sender_id,
                # "chatbot_access_token": access_token,
                # "chatbot_refresh_token": refresh_token,
                "expires_in": ACCESS_EXPIRES_MINUTES * 60  # Convert to seconds
            }
        }))

        # Set access token cookie (15 minutes)
        response.set_cookie(
            "chatbot_access_token",
            access_token,
            httponly=True,
            secure=True,  # HTTPS only in production
            samesite="None",
            max_age=ACCESS_EXPIRES_MINUTES * 60,
            path="/"
        )

        # Set refresh token cookie (30 days)
        response.set_cookie(
            "chatbot_refresh_token",
            refresh_token,
            httponly=True,
            secure=True,  # HTTPS only in production
            samesite="NOne",
            max_age=REFRESH_EXPIRES_DAYS * 24 * 60 * 60,
            path="/"
        )

        return response, 201

    except Exception as e:
        logging.error(f"Error in chatbot_init_session: {str(e)}", exc_info=True)
        return jsonify({
            "status": False,
            "message": "Failed to initialize session"
        }), 500


def chatbot_refresh_session():
    """
    SECURITY: Refresh chatbot session using refresh token

    Purpose:
    - Validates refresh token and generates new access token
    - Maintains session without re-authentication
    - Implements token rotation for security

    Request:
    - Refresh token from HttpOnly cookie or Authorization header

    Response:
    {
        "status": true,
        "message": "Session refreshed successfully",
        "data": {
            "sender_id": "uuid-here",
            "access_token": "new-jwt-token",
            "expires_in": 900
        }
    }
    """
    try:
        # Get refresh token from cookie or header
        refresh_token = request.cookies.get("chatbot_refresh_token")

        if not refresh_token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                refresh_token = auth_header.split(" ")[1]

        if not refresh_token:
            return jsonify({
                "status": False,
                "message": "Refresh token required"
            }), 401

        # Verify refresh token
        payload = verify_refresh_token_chatbot(refresh_token)
        if not payload:
            return jsonify({
                "status": False,
                "message": "Invalid or expired refresh token"
            }), 401

        sender_id = payload.get("sender_id")
        if not sender_id:
            return jsonify({
                "status": False,
                "message": "Invalid token payload"
            }), 401

        # Generate new access token
        new_access_token = generate_access_token_chatbot(sender_id)

        # SECURITY: Set new access token as HttpOnly cookie
        response = make_response(jsonify({
            "status": True,
            "message": "Session refreshed successfully",
            "data": {
                "sender_id": sender_id,
                "chatbot_access_token": new_access_token,
                "expires_in": ACCESS_EXPIRES_MINUTES * 60
            }
        }))

        response.set_cookie(
            "chatbot_access_token",
            new_access_token,
            httponly=True,
            secure=True,  # HTTPS only in production
            samesite="None",
            max_age=ACCESS_EXPIRES_MINUTES * 60,
            path="/"
        )

        logging.info(f"Session refreshed for sender: {sender_id}")

        return response, 200

    except Exception as e:
        logging.error(f"Error in chatbot_refresh_session: {str(e)}", exc_info=True)
        return jsonify({
            "status": False,
            "message": "Failed to refresh session"
        }), 500


def chatbot_validate_session():
    """
    SECURITY: Validate current chatbot session

    Purpose:
    - Checks if access token is valid
    - Returns session information
    - Used by frontend to verify authentication state

    Request:
    - Access token from HttpOnly cookie or Authorization header

    Response:
    {
        "status": true,
        "message": "Session is valid",
        "data": {
            "sender_id": "uuid-here",
            "is_valid": true,
            "expires_in": 600  // seconds remaining
        }
    }
    """
    try:
        # Get access token from cookie or header
        access_token = request.cookies.get("access_token")

        if not access_token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                access_token = auth_header.split(" ")[1]

        if not access_token:
            return jsonify({
                "status": False,
                "message": "No active session",
                "data": {
                    "is_valid": False
                }
            }), 401

        # Verify access token
        import jwt
        import os
        from datetime import datetime

        SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_IN_PROD")

        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])

            # Check if it's an access token
            if payload.get("type") != "access":
                raise jwt.InvalidTokenError("Invalid token type")

            sender_id = payload.get("sender_id")
            exp = payload.get("exp")

            # Calculate time remaining
            expires_in = max(0, exp - int(datetime.utcnow().timestamp()))

            return jsonify({
                "status": True,
                "message": "Session is valid",
                "data": {
                    "sender_id": sender_id,
                    "is_valid": True,
                    "expires_in": expires_in
                }
            }), 200

        except jwt.ExpiredSignatureError:
            return jsonify({
                "status": False,
                "message": "Session expired",
                "data": {
                    "is_valid": False,
                    "reason": "expired"
                }
            }), 401

        except jwt.InvalidTokenError as e:
            return jsonify({
                "status": False,
                "message": "Invalid session",
                "data": {
                    "is_valid": False,
                    "reason": "invalid"
                }
            }), 401

    except Exception as e:
        logging.error(f"Error in chatbot_validate_session: {str(e)}", exc_info=True)
        return jsonify({
            "status": False,
            "message": "Failed to validate session"
        }), 500


def chatbot_logout():
    """
    SECURITY: Logout chatbot session

    Purpose:
    - Clears authentication cookies
    - Invalidates current session
    - Provides clean logout mechanism

    Response:
    {
        "status": true,
        "message": "Logged out successfully"
    }
    """
    try:
        # Get sender_id from token if available for logging
        sender_id = None
        access_token = request.cookies.get("chatbot_access_token")

        if access_token:
            try:
                import jwt
                import os
                SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_IN_PROD")
                payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
                sender_id = payload.get("sender_id")
            except:
                pass

        # Create response
        response = make_response(jsonify({
            "status": True,
            "message": "Logged out successfully"
        }))

        # SECURITY: Clear authentication cookies
        response.set_cookie(
            "chatbot_access_token",
            "",
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=0  # Expire immediately
        )

        response.set_cookie(
            "chatbot_refresh_token",
            "",
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=0  # Expire immediately
        )

        if sender_id:
            logging.info(f"User logged out: {sender_id}")

        return response, 200

    except Exception as e:
        logging.error(f"Error in chatbot_logout: {str(e)}", exc_info=True)
        return jsonify({
            "status": False,
            "message": "Logout failed"
        }), 500
