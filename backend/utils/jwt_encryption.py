"""
JWT Encryption Utility using JWE (JSON Web Encryption)
Provides secure token encryption to prevent payload inspection
"""
import os
import jwt
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64
import json

# Load encryption key from environment or use default (CHANGE IN PRODUCTION!)
# ENCRYPTION_KEY = os.getenv("JWT_ENCRYPTION_KEY")

ENCRYPTION_KEY="aQ0hH3wb9jNps5srBsm3Q8Q5BZ93NE0IBDX8K8X9soQ="

if not ENCRYPTION_KEY:
    # Generate a default key (for development only)
    # In production, set JWT_ENCRYPTION_KEY in .env file
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print("WARNING: Using auto-generated JWT encryption key. Set JWT_ENCRYPTION_KEY in .env for production!")

# Ensure key is bytes
if isinstance(ENCRYPTION_KEY, str):
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()    

# Initialize Fernet cipher
cipher = Fernet(ENCRYPTION_KEY)


def encrypt_jwt_payload(jwt_token: str) -> str:
    """
    Encrypts a JWT token to prevent payload inspection

    Args:
        jwt_token: The JWT token string to encrypt

    Returns:
        Encrypted token string (base64 encoded)
    """
    try:
        # Encrypt the entire JWT token
        encrypted_bytes = cipher.encrypt(jwt_token.encode())
        # Return as base64 string for easy transmission
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    except Exception as e:
        raise ValueError(f"Failed to encrypt JWT: {str(e)}")


def decrypt_jwt_payload(encrypted_token: str) -> str:
    """
    Decrypts an encrypted JWT token

    Args:
        encrypted_token: The encrypted token string (base64 encoded)

    Returns:
        Decrypted JWT token string

    Raises:
        ValueError: If decryption fails
    """
    try:
        # Decode from base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode())
        # Decrypt to get original JWT
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt JWT: {str(e)}")


def generate_encryption_key() -> str:
    """
    Generates a new Fernet encryption key
    Use this to generate a key for your .env file

    Returns:
        Base64 encoded encryption key
    """
    return Fernet.generate_key().decode()


# Utility function for testing
if __name__ == "__main__":
    print("JWT Encryption Key Generator")
    print("=" * 50)
    key = generate_encryption_key()
    print(f"Generated Key: {key}")
    print("\nAdd this to your .env file:")
    print(f"JWT_ENCRYPTION_KEY={key}")
