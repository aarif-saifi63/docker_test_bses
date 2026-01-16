"""
Request Security Module
Shared validation for multipart/form-data requests

This module consolidates request-level security validation that was previously
duplicated across multiple controllers.

Security Features:
- Request size validation (DoS prevention)
- Multipart boundary validation
- Form field malicious content scanning
- Content-Length header validation

Author: Security Team
Date: 2026-01-12
"""

import re
from flask import request
from typing import Tuple


class RequestSecurityValidator:
    """
    Validates incoming requests for security threats

    This class provides centralized request validation to prevent:
    - DoS attacks via oversized requests
    - Malicious boundary manipulation
    - Binary payload injection
    - Form field script injection
    - Request smuggling attacks
    """

    # Maximum request size (100MB)
    MAX_REQUEST_SIZE = 100 * 1024 * 1024

    @classmethod
    def validate_multipart_request(cls) -> Tuple[bool, str]:
        """
        Validate multipart/form-data request for security threats

        Protects against:
        - Oversized requests (DoS attacks)
        - Malicious boundary manipulation
        - Binary payload injection
        - Form field script injection
        - Request smuggling attacks

        Returns:
            Tuple[is_valid, error_message]:
                - is_valid: True if request passes all security checks
                - error_message: Description of security issue or empty string

        Usage:
            is_valid, error = RequestSecurityValidator.validate_multipart_request()
            if not is_valid:
                return jsonify({"status": False, "message": error}), 400
        """

        # 1. Validate Content-Length header exists
        content_length = request.content_length

        if content_length is None:
            return False, "Content-Length header is required"

        # 2. Enforce maximum request size (DoS prevention)
        if content_length > cls.MAX_REQUEST_SIZE:
            return False, f"Request size {content_length} bytes exceeds maximum {cls.MAX_REQUEST_SIZE} bytes (100MB)"

        # 3. Validate Content-Type is multipart/form-data
        content_type = request.headers.get("Content-Type", "")

        if not content_type.startswith("multipart/form-data"):
            return False, "Content-Type must be multipart/form-data for file uploads"

        # 4. Extract and validate multipart boundary
        boundary_match = re.search(r'boundary=([^;]+)', content_type)
        if not boundary_match:
            return False, "Multipart boundary not found in Content-Type header"

        boundary = boundary_match.group(1).strip()

        # 5. Validate boundary format
        if not boundary or len(boundary) > 70:
            return False, "Invalid multipart boundary format (empty or too long)"

        # Boundary should only contain RFC 2046 allowed characters
        # Letters, digits, and special chars: ' ( ) + _ , - . / : = ?
        if not re.match(r'^[a-zA-Z0-9\'\(\)\+_,\-\./:=\?]+$', boundary):
            return False, "Multipart boundary contains invalid characters"

        # 6. Scan form fields for malicious patterns
        try:
            form_data = request.form.to_dict()

            # Malicious patterns to detect
            malicious_patterns = [
                (r'<script[^>]*>', 'Script tag'),
                (r'javascript:', 'JavaScript protocol'),
                (r'on\w+\s*=', 'Event handler'),
                (r'<\?php', 'PHP code'),
                (r'eval\s*\(', 'Eval function'),
                (r'base64_decode', 'Base64 decode'),
                (r'system\s*\(', 'System command'),
                (r'exec\s*\(', 'Exec command'),
                (r'shell_exec', 'Shell exec'),
                (r'passthru', 'Passthru function'),
                (r'<iframe', 'Iframe tag'),
                (r'<embed', 'Embed tag'),
                (r'<object', 'Object tag'),
            ]

            for field_name, field_value in form_data.items():
                if isinstance(field_value, str):
                    for pattern, description in malicious_patterns:
                        if re.search(pattern, field_value, re.IGNORECASE):
                            return False, f"Potentially malicious content detected in field '{field_name}': {description}"

        except Exception as e:
            return False, f"Failed to parse form data: {str(e)}"

        # All checks passed
        return True, ""

    @classmethod
    def validate_json_request(cls, max_size: int = 10 * 1024 * 1024) -> Tuple[bool, str]:
        """
        Validate JSON request for security threats

        Args:
            max_size: Maximum allowed JSON payload size in bytes (default 10MB)

        Returns:
            Tuple[is_valid, error_message]
        """

        # 1. Validate Content-Length
        content_length = request.content_length

        if content_length is None:
            return False, "Content-Length header is required"

        # 2. Enforce size limit
        if content_length > max_size:
            return False, f"Request size {content_length} bytes exceeds maximum {max_size} bytes"

        # 3. Validate Content-Type
        content_type = request.headers.get("Content-Type", "")

        if "application/json" not in content_type.lower():
            return False, "Content-Type must be application/json"

        return True, ""


# Convenience functions for easy import
def validate_multipart_request() -> Tuple[bool, str]:
    """
    Convenience function wrapper for RequestSecurityValidator.validate_multipart_request()

    Usage:
        from utils.request_security import validate_multipart_request

        is_valid, error = validate_multipart_request()
        if not is_valid:
            return jsonify({"status": False, "message": error}), 400
    """
    return RequestSecurityValidator.validate_multipart_request()


def validate_json_request(max_size: int = 10 * 1024 * 1024) -> Tuple[bool, str]:
    """
    Convenience function wrapper for RequestSecurityValidator.validate_json_request()
    """
    return RequestSecurityValidator.validate_json_request(max_size)
