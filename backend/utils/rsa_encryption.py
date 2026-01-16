"""
RSA Encryption Utility for Secure Login
SECURITY: Protects credentials in transit using RSA public/private key encryption

This module provides:
- RSA key pair generation and storage
- Public key endpoint for frontend
- Decryption of encrypted login credentials
"""

import os
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

# Path to store RSA keys
KEY_DIR = os.path.join(os.path.dirname(__file__), "..", "keys")
PRIVATE_KEY_PATH = os.path.join(KEY_DIR, "rsa_private.pem")
PUBLIC_KEY_PATH = os.path.join(KEY_DIR, "rsa_public.pem")

# RSA key size (2048 bits is secure and fast)
KEY_SIZE = 2048


def ensure_keys_exist():
    """
    SECURITY: Ensure RSA key pair exists, generate if not found

    Keys are stored in PEM format:
    - Private key: Used by backend to decrypt credentials
    - Public key: Sent to frontend to encrypt credentials
    """
    os.makedirs(KEY_DIR, exist_ok=True)

    if os.path.exists(PRIVATE_KEY_PATH) and os.path.exists(PUBLIC_KEY_PATH):
        logger.info("RSA keys already exist")
        return

    logger.info("Generating new RSA key pair...")

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=KEY_SIZE,
        backend=default_backend()
    )

    # Extract public key
    public_key = private_key.public_key()

    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()  # No password protection
    )

    # Serialize public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Save keys to files
    with open(PRIVATE_KEY_PATH, 'wb') as f:
        f.write(private_pem)
        os.chmod(PRIVATE_KEY_PATH, 0o600)  # Read/write for owner only

    with open(PUBLIC_KEY_PATH, 'wb') as f:
        f.write(public_pem)
        os.chmod(PUBLIC_KEY_PATH, 0o644)  # Read for all

    logger.info(f"RSA keys generated successfully at {KEY_DIR}")


def load_private_key():
    """
    Load RSA private key from file

    Returns:
        RSAPrivateKey object
    """
    ensure_keys_exist()

    with open(PRIVATE_KEY_PATH, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )

    return private_key


def load_public_key():
    """
    Load RSA public key from file

    Returns:
        RSAPublicKey object
    """
    ensure_keys_exist()

    with open(PUBLIC_KEY_PATH, 'rb') as f:
        public_key = serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )

    return public_key


def get_public_key_string():
    """
    Get public key as string for sending to frontend

    Returns:
        str: PEM-formatted public key
    """
    ensure_keys_exist()

    with open(PUBLIC_KEY_PATH, 'r') as f:
        return f.read()


def decrypt_data(encrypted_data_b64):
    """
    SECURITY: Decrypt RSA-encrypted data from frontend

    Args:
        encrypted_data_b64 (str): Base64-encoded encrypted data

    Returns:
        str: Decrypted plaintext data

    Raises:
        ValueError: If decryption fails (invalid data or wrong key)
    """
    try:
        # Load private key
        private_key = load_private_key()

        # Decode base64
        encrypted_data = base64.b64decode(encrypted_data_b64)

        # Decrypt using RSA-OAEP padding (secure padding scheme)
        decrypted_data = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Convert bytes to string
        return decrypted_data.decode('utf-8')

    except Exception as e:
        logger.error(f"RSA decryption failed: {str(e)}")
        raise ValueError("Failed to decrypt data. Invalid encryption or corrupted data.")


def encrypt_data(plaintext):
    """
    SECURITY: Encrypt data using RSA public key (for testing)

    Args:
        plaintext (str): Data to encrypt

    Returns:
        str: Base64-encoded encrypted data
    """
    try:
        # Load public key
        public_key = load_public_key()

        # Encrypt using RSA-OAEP padding
        encrypted_data = public_key.encrypt(
            plaintext.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Encode to base64 for transport
        return base64.b64encode(encrypted_data).decode('utf-8')

    except Exception as e:
        logger.error(f"RSA encryption failed: {str(e)}")
        raise ValueError("Failed to encrypt data")


# Initialize keys on module import
ensure_keys_exist()
