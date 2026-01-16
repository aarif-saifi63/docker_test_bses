"""
Secure File Download Controller with Signed URLs
Addresses VAPT finding: Unauthenticated File Access (CWE-284)

This module provides:
1. Time-limited signed URLs for file downloads
2. HMAC-based signature validation
3. Path traversal protection
4. Optional one-time use tokens via Redis

Supported File Types:
- Images: PNG, JPG, JPEG
- Documents: PDF, DOC, DOCX
- Videos: MP4, MKV, WEBM, AVI

Note: File extensions and MIME types match those defined in ad_controller.py
to ensure consistency across the application.
"""

import os
import time
import hmac
import hashlib
import base64
import urllib.parse
from pathlib import Path
from flask import Blueprint, current_app, request, jsonify, send_file
from werkzeug.exceptions import BadRequest, NotFound, Forbidden
import logging

from middlewares.auth_middleware import flexible_token_required

bp = Blueprint("signed_downloads", __name__)

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# File extension to MIME type mapping
# Matches the allowed extensions from ad_controller.py
EXTENSION_MIME_TYPES = {
    # Images (from ALLOWED_EXTENSIONS["image"])
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    # Documents (from ALLOWED_EXTENSIONS["document"])
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    # Videos (from ALLOWED_EXTENSIONS["video"])
    'mp4': 'video/mp4',
    'mkv': 'video/x-matroska',
    'webm': 'video/webm',
    'avi': 'video/x-msvideo',
}

# Extensions that should be displayed inline (not downloaded)
INLINE_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # Images

def _b64url_encode(raw: bytes) -> str:
    """Base64 URL-safe encoding without padding"""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

def _sign_message(secret: str, message: bytes) -> str:
    """Generate HMAC-SHA256 signature for message"""
    mac = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(mac)

def _resolve_and_check(root: str, rel_path: str):
    """
    Resolve file path and validate it's within allowed directory
    Protects against path traversal attacks (CWE-22)
    """
    try:
        # Normalize the root path
        root_path = Path(root).resolve()

        # Construct the full path
        full_path = (root_path / rel_path).resolve()

        # Security check: Ensure file is within root directory
        if not str(full_path).startswith(str(root_path)):
            logging.warning(f"Path traversal attempt detected: {rel_path}")
            return None

        # Check file exists and is a regular file
        if not full_path.exists() or not full_path.is_file():
            logging.warning(f"File not found or not a regular file: {full_path}")
            return None

        return str(full_path)
    except Exception as e:
        logging.error(f"Error resolving path {rel_path}: {str(e)}")
        return None

@bp.route("/generate_signed_url", methods=["POST"])
def generate_signed_url():
    """
    Generate a signed URL for file download

    Request JSON:
    {
        "file": "relative/path/to/file.pdf",
        "expires_in": 300  # seconds (optional, default from config)
    }

    Response:
    {
        "url": "http://host/files/download?file=...&expires=...&sig=...",
        "expires_at": 1234567890
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        file_rel = data.get("file")
        expires_in = int(data.get("expires_in", current_app.config.get("DEFAULT_EXPIRY", 300)))

        if not file_rel:
            raise BadRequest("'file' parameter is required")

        # Validate expires_in range
        max_expiry = current_app.config.get("MAX_EXPIRY", 3600)
        if expires_in <= 0 or expires_in > max_expiry:
            raise BadRequest(f"expires_in must be between 1 and {max_expiry} seconds")

        # Get files root from config
        files_root = current_app.config.get("FILES_ROOT", os.path.join(os.getcwd(), "Media"))

        # Validate file exists and is within allowed directory
        resolved = _resolve_and_check(files_root, file_rel)
        if not resolved:
            raise NotFound("File not found or access denied")

        # Generate expiry timestamp
        expires_ts = int(time.time()) + expires_in

        # Create signature: HMAC(secret, "file|expires")
        msg = f"{file_rel}|{expires_ts}".encode("utf-8")
        sig = _sign_message(current_app.config["SECRET_KEY"], msg)

        # Optional: Store in Redis for one-time use enforcement
        redis_client = current_app.extensions.get("redis_client")
        if redis_client:
            try:
                redis_client.setex(f"signedurl:{sig}", expires_in, "1")
                logging.info(f"Signed URL cached in Redis: {sig[:8]}...")
            except Exception as e:
                logging.warning(f"Redis caching failed: {str(e)}")

        # Build download URL
        host = request.host_url.rstrip("/")
        download_path = current_app.config.get('SIGNED_DOWNLOAD_PATH', '/files/download')
        qs = urllib.parse.urlencode({
            "file": file_rel,
            "expires": str(expires_ts),
            "sig": sig
        })
        url = f"{host}{download_path}?{qs}"
        
        print(f"Generated signed URL for: {file_rel} (expires in {expires_in}s)")
        logging.info(f"Generated signed URL for: {file_rel} (expires in {expires_in}s)")

        return jsonify({
            "status": True,
            "url": url,
            "expires_at": expires_ts,
            "expires_in": expires_in
        }), 200

    except BadRequest as e:
        return jsonify({"status": False, "message": str(e)}), 400
    except NotFound as e:
        return jsonify({"status": False, "message": str(e)}), 404
    except Exception as e:
        logging.error(f"Error generating signed URL: {str(e)}", exc_info=True)
        return jsonify({"status": False, "message": "Internal server error"}), 500

@bp.route("/download", methods=["GET"])
@flexible_token_required  # Change decorator
def download():
    """
    Download file using signed URL

    Query Parameters:
    - file: relative file path
    - expires: expiry timestamp
    - sig: HMAC signature

    Security features:
    1. Time-based expiration
    2. HMAC signature validation
    3. Optional one-time use (via Redis)
    4. Path traversal protection
    """
    try:
        file_rel = request.args.get("file")
        expires = request.args.get("expires")
        sig = request.args.get("sig")

        if not file_rel or not expires or not sig:
            raise BadRequest("Missing required parameters (file, expires, sig)")

        # Parse and validate expiry timestamp
        try:
            expires_ts = int(expires)
        except ValueError:
            raise BadRequest("Invalid expires parameter")

        # Check if URL has expired
        if time.time() > expires_ts:
            logging.warning(f"Expired download attempt for: {file_rel}")
            raise Forbidden("Download link has expired")

        # Optional: Redis one-time use enforcement (atomic check+delete)
        redis_client = current_app.extensions.get("redis_client")
        if redis_client:
            key = f"signedurl:{sig}"
            # Lua script for atomic GET + DELETE
            LUA_SCRIPT = """
            if redis.call('get', KEYS[1]) then
                redis.call('del', KEYS[1])
                return 1
            else
                return 0
            end
            """
            try:
                result = redis_client.eval(LUA_SCRIPT, 1, key)
                if result != 1:
                    logging.warning(f"Invalid or reused download link: {sig[:8]}...")
                    raise Forbidden("Download link is invalid or has already been used")
            except Exception as e:
                logging.error(f"Redis validation failed: {str(e)}")
                # Fail closed: reject if Redis check fails
                raise Forbidden("Unable to validate download link")

        # Verify HMAC signature
        msg = f"{file_rel}|{expires_ts}".encode("utf-8")
        expected_sig = _sign_message(current_app.config["SECRET_KEY"], msg)

        if not hmac.compare_digest(expected_sig, sig):
            logging.warning(f"Invalid signature for file: {file_rel}")
            raise Forbidden("Invalid download signature")

        # Resolve and validate file path
        files_root = current_app.config.get("FILES_ROOT", os.path.join(os.getcwd(), "Media"))
        resolved = _resolve_and_check(files_root, file_rel)

        if not resolved:
            raise NotFound("File not found")

        # Get filename and determine file type
        filename = Path(resolved).name
        file_ext = Path(resolved).suffix.lstrip('.').lower()

        # Get MIME type from our extension mapping
        mimetype = EXTENSION_MIME_TYPES.get(file_ext, 'application/octet-stream')

        # Determine if file should be displayed inline (images) or as download
        is_inline = file_ext in INLINE_EXTENSIONS

        # Send file with security headers
        response = send_file(
            resolved,
            as_attachment=not is_inline,  # Images inline, documents/videos as download
            download_name=filename,
            mimetype=mimetype,
            conditional=True
        )

        # Add security headers
        response.headers["Cache-Control"] = "no-store, no-cache, private, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        logging.info(f"File downloaded successfully: {file_rel}")
        return response

    except BadRequest as e:
        return jsonify({"status": False, "message": str(e)}), 400
    except Forbidden as e:
        return jsonify({"status": False, "message": str(e)}), 403
    except NotFound as e:
        return jsonify({"status": False, "message": str(e)}), 404
    except Exception as e:
        logging.error(f"Error in download: {str(e)}", exc_info=True)
        return jsonify({"status": False, "message": "Internal server error"}), 500
