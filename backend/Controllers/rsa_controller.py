"""
RSA Public Key Controller
Provides RSA public key to frontend for encrypting login credentials
"""

from flask import jsonify
from utils.rsa_encryption import get_public_key_string
import logging

logger = logging.getLogger(__name__)


def get_public_key():
    """
    SECURITY: Provide RSA public key to frontend

    This endpoint is PUBLIC and does not require authentication.
    The public key is safe to expose - it can only encrypt, not decrypt.

    Returns:
        JSON response with public key in PEM format

    Example Response:
        {
            "status": true,
            "message": "Public key retrieved successfully",
            "public_key": "-----BEGIN PUBLIC KEY-----\n..."
        }
    """
    try:
        public_key_pem = get_public_key_string()

        return jsonify({
            "status": True,
            "message": "Public key retrieved successfully",
            "public_key": public_key_pem
        }), 200

    except Exception as e:
        logger.error(f"Failed to retrieve public key: {str(e)}")
        return jsonify({
            "status": False,
            "message": "Failed to retrieve public key"
        }), 500
