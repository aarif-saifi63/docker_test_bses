"""
FileSecurityHelper - Robust File Security Validation Module
Based on VAPT security requirements and OWASP best practices

Security Features:
- File size validation
- Magic number (file signature) validation
- MIME type validation
- Double extension detection
- Malicious content scanning
- PDF script/JavaScript detection
- Path traversal prevention
- Null byte injection prevention

Supported File Types:
- PDF: application/pdf
- DOCX: application/vnd.openxmlformats-officedocument.wordprocessingml.document
- DOCM: application/vnd.ms-word.document.macroEnabled.12
- DOC: application/msword
- VSDX: application/vnd.ms-visio.drawing
- VSDM: application/vnd.ms-visio.drawing.macroEnabled.12
- VSD: application/vnd.visio
- Images: PNG, JPG, JPEG
- Videos: MP4, MKV, WEBM, AVI
"""

import os
import re
import magic
import uuid
from typing import Tuple, List, Dict, Optional


class FileSecurityHelper:
    """
    Comprehensive file security validation helper class
    Protects against file upload attacks and VAPT vulnerabilities
    """

    # 10 MB Limit for documents
    MAX_FILE_SIZE = 10 * 1024 * 1024

    # File categories with size limits
    FILE_CATEGORIES = {
        "image": {
            "extensions": {".png", ".jpg", ".jpeg", ".svg"},
            "max_size": 5 * 1024 * 1024  # 5MB
        },
        "document": {
            "extensions": {".pdf", ".doc", ".docx", ".docm", ".vsd", ".vsdx", ".vsdm"},
            "max_size": 10 * 1024 * 1024  # 10MB
        },
        "video": {
            "extensions": {".mp4", ".mkv", ".webm", ".avi"},
            "max_size": 50 * 1024 * 1024  # 50MB
        }
    }

    # Magic Numbers (File Signatures)
    SIG_PDF = b'\x25\x50\x44\x46'  # %PDF
    SIG_ZIP = b'\x50\x4B\x03\x04'  # PK.. (used by DOCX, VSDX)
    SIG_OLE = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'  # OLE format (DOC, VSD)
    SIG_PNG = b'\x89PNG\r\n\x1a\n'
    SIG_JPG = b'\xff\xd8\xff'
    SIG_SVG_XML = b'<?xml'
    SIG_SVG = b'<svg'
    SIG_MP4 = b'\x00\x00\x00'
    SIG_MKV = b'\x1A\x45\xDF\xA3'
    SIG_WEBM = b'\x1A\x45\xDF\xA3'
    SIG_AVI = b'RIFF'

    # Extension → Valid Magic Numbers mapping
    ALLOWED_EXTENSIONS: Dict[str, List[bytes]] = {
        # Documents
        ".pdf": [SIG_PDF],
        ".docx": [SIG_ZIP],
        ".docm": [SIG_ZIP],
        ".doc": [SIG_OLE],
        ".vsdx": [SIG_ZIP],
        ".vsdm": [SIG_ZIP],
        ".vsd": [SIG_OLE],

        # Images
        ".png": [SIG_PNG],
        ".jpg": [SIG_JPG],
        ".jpeg": [SIG_JPG],
        ".svg": [SIG_SVG_XML, SIG_SVG],

        # Videos
        ".mp4": [SIG_MP4],
        ".mkv": [SIG_MKV],
        ".webm": [SIG_WEBM],
        ".avi": [SIG_AVI],
    }

    # Extension → Allowed MIME Types (Advisory validation)
    ALLOWED_CONTENT_TYPES: Dict[str, List[str]] = {
        # Documents
        ".pdf": ["application/pdf"],
        ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        ".docm": ["application/vnd.ms-word.document.macroEnabled.12"],
        ".doc": ["application/msword"],
        ".vsdx": [
            "application/vnd.ms-visio.drawing",
            "application/octet-stream"
        ],
        ".vsdm": [
            "application/vnd.ms-visio.drawing.macroEnabled.12",
            "application/octet-stream"
        ],
        ".vsd": [
            "application/vnd.visio",
            "application/x-visio",
            "application/msword",
            "application/octet-stream",
            "application/vnd.ms-visio.viewer"
        ],

        # Images
        ".png": ["image/png"],
        ".jpg": ["image/jpeg"],
        ".jpeg": ["image/jpeg"],
        ".svg": ["image/svg+xml"],

        # Videos
        ".mp4": ["video/mp4"],
        ".mkv": ["video/x-matroska"],
        ".webm": ["video/webm"],
        ".avi": ["video/x-msvideo"],
    }

    @classmethod
    def is_valid_file(cls, file, content_type: str, max_size: int = None) -> Tuple[bool, str]:
        """
        Comprehensive file validation with all security checks

        Args:
            file: File object (Flask/Werkzeug FileStorage)
            content_type: MIME type from request header
            max_size: Maximum file size in bytes (optional, defaults to MAX_FILE_SIZE)

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        error_message = ""

        # 1. Basic checks
        if not file or not file.filename:
            return False, "File is empty or no filename provided"

        # 2. File size check (CRITICAL: Check before reading entire file)
        max_allowed_size = max_size or cls.MAX_FILE_SIZE
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size == 0:
            return False, "File is empty"

        # Strict size enforcement
        if file_size > max_allowed_size:
            size_mb = file_size / (1024 * 1024)
            limit_mb = max_allowed_size / (1024 * 1024)
            return False, f"File size ({size_mb:.2f}MB) exceeds maximum allowed size of {limit_mb:.0f}MB"

        # Additional safety check: Reject extremely large files immediately
        # This prevents DoS attacks before we read the content
        absolute_max = 100 * 1024 * 1024  # 100MB absolute maximum
        if file_size > absolute_max:
            return False, f"File size ({file_size / (1024 * 1024):.2f}MB) exceeds absolute maximum of 100MB"

        # 3. Double extension check
        if cls._has_double_extension(file.filename):
            return False, "Double extensions are not allowed"

        # 4. Extension allowlist
        ext = os.path.splitext(file.filename)[1].lower()
        if not ext or ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"Unsupported file type: {ext}"

        # 5. Read file content
        try:
            file.seek(0)
            file_bytes = file.read()
            file.seek(0)
        except Exception as e:
            return False, f"Unable to read file content: {str(e)}"

        # 6. Magic number validation (CRITICAL SECURITY CHECK)
        if not cls._validate_magic_bytes(file_bytes, ext):
            return False, "File signature mismatch (spoofing detected)"

        # 7. MIME type validation
        if ext in cls.ALLOWED_CONTENT_TYPES:
            allowed_types = cls.ALLOWED_CONTENT_TYPES[ext]
            if not any(ct.lower() == content_type.lower() for ct in allowed_types):
                return False, f"Invalid Content-Type '{content_type}' for extension '{ext}'"

        # 8. PDF script/JavaScript detection (VAPT requirement)
        if ext == ".pdf":
            if cls._pdf_contains_script_like_content(file_bytes):
                return False, "PDF contains embedded scripts or active content and is not allowed"

        # 9. SVG sanitization and validation (XSS/XXE protection)
        if ext == ".svg":
            is_safe, svg_error = cls._validate_svg_content(file_bytes)
            if not is_safe:
                return False, f"SVG validation failed: {svg_error}"

        # 10. General malicious content scan
        if not cls._scan_content(file_bytes, file.filename):
            return False, "Malicious content detected in file"

        return True, ""

    @classmethod
    def _has_double_extension(cls, filename: str) -> bool:
        """
        Check for double extension attacks

        Examples:
        - file.php.pdf ❌
        - file.exe.docx ❌
        - document.pdf ✅
        """
        if not filename:
            return True

        filename = os.path.basename(filename)
        dot_count = filename.count('.')

        return dot_count > 1

    @classmethod
    def _validate_magic_bytes(cls, file_bytes: bytes, ext: str) -> bool:
        """
        Validate file signature (magic bytes) against extension

        Enhanced validation to detect polyglot files:
        - Checks primary magic bytes match extension
        - Detects conflicting signatures (polyglot attacks)
        - Validates file structure integrity

        This is a CRITICAL security check - prevents content spoofing
        """
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False

        if len(file_bytes) < 8:
            return False

        header = file_bytes[:min(512, len(file_bytes))]  # Check first 512 bytes
        valid_signatures = cls.ALLOWED_EXTENSIONS[ext]

        # First, verify the file starts with a valid signature for its extension
        signature_match = False
        for sig in valid_signatures:
            if header[:len(sig)] == sig:
                signature_match = True
                break

        if not signature_match:
            return False

        # Additional polyglot detection: Check for conflicting signatures
        # Images should NOT contain document signatures
        if ext in {".png", ".jpg", ".jpeg"}:
            # Reject if contains signatures of other file types
            forbidden_sigs = [
                b'%PDF',           # PDF signature
                b'PK\x03\x04',     # ZIP/Office signature
                b'\xD0\xCF\x11\xE0',  # OLE/Office signature
                b'MZ',             # Executable signature
                b'<!DOCTYPE',      # HTML signature
                b'<html',          # HTML signature
            ]
            for forbidden_sig in forbidden_sigs:
                if forbidden_sig in header:
                    return False

        # PDFs should have proper structure
        if ext == ".pdf":
            # Must start with %PDF and should have %%EOF somewhere
            if not file_bytes.startswith(b'%PDF'):
                return False
            # Additional validation: PDF version should be readable
            if not any(file_bytes.startswith(ver) for ver in [
                b'%PDF-1.0', b'%PDF-1.1', b'%PDF-1.2', b'%PDF-1.3',
                b'%PDF-1.4', b'%PDF-1.5', b'%PDF-1.6', b'%PDF-1.7',
                b'%PDF-2.0'
            ]):
                return False

        # JPEG should have proper structure (starts with FFD8FF, ends with FFD9)
        if ext in {".jpg", ".jpeg"}:
            if not file_bytes.startswith(b'\xff\xd8\xff'):
                return False
            # Large JPEGs should have FFD9 end marker
            if len(file_bytes) > 1000 and not file_bytes.endswith(b'\xff\xd9'):
                # Some JPEGs might have trailing data, check if FFD9 exists somewhere
                if b'\xff\xd9' not in file_bytes[-100:]:
                    return False

        # PNG should have IEND chunk at the end
        if ext == ".png":
            if not file_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
                return False
            # PNG must end with IEND chunk
            if len(file_bytes) > 1000 and b'IEND' not in file_bytes[-100:]:
                return False

        return True

    @classmethod
    def _pdf_contains_script_like_content(cls, pdf_bytes: bytes) -> bool:
        """
        Scan PDF for JavaScript, auto-execution, and malicious patterns

        Detects:
        - /JavaScript - Embedded JS in PDF
        - /JS - JavaScript abbreviation
        - /OpenAction - Auto-executes when PDF opens
        - /AA - Additional Actions (auto-execution)
        - /Launch - Tries to launch external programs
        - /SubmitForm - Tries to send data to external URL
        - /RichMedia - Can contain Flash/JS payloads
        """
        # Convert to ASCII string for pattern matching
        content = pdf_bytes.decode('ascii', errors='ignore')

        # Remove compressed streams to avoid false positives
        content = re.sub(
            r'stream[\s\S]*?endstream',
            '',
            content,
            flags=re.IGNORECASE
        )

        forbidden_patterns = [
            "/JavaScript",
            "/JS",
            "/OpenAction",
            "/AA",
            "/Launch",
            "/SubmitForm",
            "/RichMedia"
        ]

        for pattern in forbidden_patterns:
            if pattern.lower() in content.lower():
                return True

        return False

    @classmethod
    def _scan_content(cls, content: bytes, filename: str) -> bool:
        """
        Scan file content for webshell / script injection patterns

        Enhanced to detect polyglot attacks and embedded malicious code

        Protects against:
        - PHP webshells embedded in images
        - Polyglot files (valid as multiple formats)
        - Embedded scripts in any file type
        - Command injection patterns
        """
        ext = os.path.splitext(filename)[1].lower()

        # Scan entire file content for malicious patterns
        # Note: We scan ALL files, including images, to detect polyglot attacks
        data = content.decode("utf-8", errors="ignore").lower()

        # Critical malicious patterns that should NEVER appear in legitimate files
        malicious_patterns = [
            r"<\?php",              # PHP tags
            r"<%.*%>",              # ASP/JSP tags
            r"eval\s*\(",           # Eval functions
            r"base64_decode\s*\(",  # Base64 decode (common in obfuscation)
            r"shell_exec\s*\(",     # Shell execution
            r"system\s*\(",         # System calls
            r"passthru\s*\(",       # Command execution
            r"exec\s*\(",           # Exec functions
            r"assert\s*\(",         # Assert (can be used for code injection)
            r"popen\s*\(",          # Process execution
            r"proc_open\s*\(",      # Process control
            r"pcntl_exec\s*\(",     # Process control
            r"cmd\.exe",            # Windows command execution
            r"/bin/(ba)?sh",        # Unix shell execution
        ]

        for pattern in malicious_patterns:
            if re.search(pattern, data):
                return False

        # Additional check for images: detect embedded PDF signatures (polyglot attack)
        if ext in {".png", ".jpg", ".jpeg"}:
            # Check if image contains PDF signature (polyglot attack indicator)
            if b'%PDF' in content:
                return False
            # Check for HTML/XML in images
            if b'<html' in content.lower() or b'<body' in content.lower():
                return False

        return True

    @classmethod
    def _validate_svg_content(cls, svg_bytes: bytes) -> Tuple[bool, str]:
        """
        Validate and sanitize SVG content for security threats

        Protects against:
        - XSS attacks (embedded JavaScript)
        - XXE attacks (external entity injection)
        - Event handlers (onclick, onload, etc.)
        - External resource loading

        Returns:
            Tuple[bool, str]: (is_safe, error_message)
        """
        try:
            from lxml import etree
        except ImportError:
            # If lxml is not available, use basic string-based validation
            return cls._validate_svg_basic(svg_bytes)

        try:
            # Parse with secure settings
            parser = etree.XMLParser(
                resolve_entities=False,  # Prevent XXE
                no_network=True,         # Prevent external resource loading
                remove_comments=True,    # Remove comments
                dtd_validation=False,    # No DTD validation
                load_dtd=False          # Don't load DTD
            )

            root = etree.fromstring(svg_bytes, parser)

            # Verify root is SVG
            if not root.tag.endswith("svg") and root.tag != "{http://www.w3.org/2000/svg}svg":
                return False, "Invalid SVG root element"

            # Check for dangerous elements and attributes
            dangerous_attrs = ['onload', 'onerror', 'onclick', 'onmouseover', 'onmouseout',
                             'onmousemove', 'onmouseenter', 'onmouseleave', 'onfocus', 'onblur']

            for el in root.iter():
                # Remove event handler attributes
                for attr in list(el.attrib):
                    if attr.lower().startswith("on"):
                        return False, f"Event handler detected: {attr}"

                    # Check for javascript: protocol
                    attr_value = el.attrib.get(attr, "").lower()
                    if "javascript:" in attr_value:
                        return False, "JavaScript protocol detected in attribute"

                    # Check for data: URIs with scripts
                    if "data:" in attr_value and "script" in attr_value:
                        return False, "Suspicious data URI detected"

                # Block script elements
                if "script" in el.tag.lower():
                    return False, "Script element detected in SVG"

            return True, ""

        except etree.XMLSyntaxError as e:
            return False, f"Invalid XML syntax: {str(e)}"
        except Exception as e:
            return False, f"SVG validation error: {str(e)}"

    @classmethod
    def _validate_svg_basic(cls, svg_bytes: bytes) -> Tuple[bool, str]:
        """
        Basic SVG validation when lxml is not available

        Uses string-based pattern matching
        """
        try:
            svg_content = svg_bytes.decode('utf-8', errors='ignore').lower()
        except Exception:
            return False, "Unable to decode SVG content"

        # Check for dangerous patterns
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',  # Event handlers
            r'<iframe',
            r'<embed',
            r'<object',
            r'xlink:href\s*=\s*["\']javascript:',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, svg_content, re.IGNORECASE):
                return False, f"Dangerous pattern detected: {pattern}"

        return True, ""

    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        """
        Validate filename against path traversal and null byte attacks

        Protects against:
        - Path traversal (../../etc/passwd)
        - Null byte injection (file.pdf%00.php)
        - Invalid characters
        """
        if not filename or "." not in filename:
            return False

        # Path traversal check
        if "/" in filename or "\\" in filename or ".." in filename:
            return False

        # Null byte injection check
        if "\x00" in filename or "%00" in filename:
            return False

        # Check extension is in allowed list
        ext = os.path.splitext(filename)[1].lower()
        return ext in cls.ALLOWED_EXTENSIONS

    @classmethod
    def get_file_category(cls, filename: str) -> Tuple[Optional[str], int]:
        """
        Determine file category and max size from filename

        Args:
            filename: Name of the file

        Returns:
            Tuple[category, max_size]: Category name and size limit in bytes
                                       Returns (None, MAX_FILE_SIZE) if not found
        """
        ext = os.path.splitext(filename)[1].lower()

        for category, config in cls.FILE_CATEGORIES.items():
            if ext in config["extensions"]:
                return category, config["max_size"]

        return None, cls.MAX_FILE_SIZE

    @classmethod
    def validate_and_save_file(
        cls,
        file,
        upload_dir: str,
        allowed_categories: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Complete file validation and secure save operation

        This is the ONLY method endpoints should call for file uploads!
        Consolidates ALL security checks and file saving logic.

        Args:
            file: FileStorage object from Flask request
            upload_dir: Directory to save file (will be created if missing)
            allowed_categories: Optional list of allowed categories (e.g., ["image", "document"])

        Returns:
            Tuple[success, filepath_relative, error_message]
            - success: True if file validated and saved successfully
            - filepath_relative: Relative path like "ad_content/uuid.pdf" or None
            - error_message: Error description or None if successful

        Security Features:
        - All validations from is_valid_file()
        - Category-based size limits
        - Random UUID filename (prevents overwrites & guessing)
        - Secure file permissions (0o644)
        - Post-save MIME verification using python-magic
        - Directory traversal prevention
        - Atomic save operation (cleanup on failure)
        """

        # 1. Basic validation
        if not file or not file.filename:
            return False, None, "No file provided"

        # 2. Determine category and size limit
        category, max_size = cls.get_file_category(file.filename)

        if category is None:
            return False, None, f"Unsupported file type"

        # 3. Check if category is allowed (if restriction specified)
        if allowed_categories and category not in allowed_categories:
            return False, None, f"File category '{category}' not allowed. Allowed: {', '.join(allowed_categories)}"

        # 4. Get content type
        content_type = file.content_type if hasattr(file, 'content_type') else 'application/octet-stream'

        # 5. Perform comprehensive validation using is_valid_file()
        is_valid, error_message = cls.is_valid_file(file, content_type, max_size)

        if not is_valid:
            return False, None, error_message

        # 6. Extract extension
        ext = os.path.splitext(file.filename)[1].lower()

        # 7. Generate secure random filename
        secure_filename = f"{uuid.uuid4()}{ext}"

        # 8. Ensure upload directory exists
        try:
            os.makedirs(upload_dir, exist_ok=True)
        except Exception as e:
            return False, None, f"Failed to create upload directory: {str(e)}"

        # 9. Build full path
        full_path = os.path.join(upload_dir, secure_filename)

        # 10. Save file atomically
        try:
            file.seek(0)
            file.save(full_path)
        except Exception as e:
            return False, None, f"Failed to save file: {str(e)}"

        # 11. Set secure file permissions (read-only for group/others)
        try:
            os.chmod(full_path, 0o644)
        except Exception:
            pass  # Permissions may fail on Windows, but that's okay

        # 12. Post-save MIME verification using python-magic (defense in depth)
        try:
            mime = magic.from_file(full_path, mime=True)

            # Verify MIME matches extension
            if ext in cls.ALLOWED_CONTENT_TYPES:
                allowed_mimes = cls.ALLOWED_CONTENT_TYPES[ext]
                if mime not in allowed_mimes:
                    # Cleanup failed file
                    try:
                        os.remove(full_path)
                    except:
                        pass
                    return False, None, f"Post-save MIME verification failed. Expected {allowed_mimes}, got {mime}"
        except Exception as e:
            # Cleanup on error
            try:
                os.remove(full_path)
            except:
                pass
            return False, None, f"Post-save verification failed: {str(e)}"

        # 13. Return relative path (for database storage)
        # Assuming upload_dir is like "/path/to/uploads/ad_content"
        # We want to return "ad_content/uuid.ext"
        relative_path = os.path.join(os.path.basename(upload_dir), secure_filename)

        return True, relative_path, None


# Convenience function for backward compatibility
def is_valid_file(file, content_type: str, max_size: int = None) -> Tuple[bool, str]:
    """
    Convenience function wrapper for FileSecurityHelper.is_valid_file
    """
    return FileSecurityHelper.is_valid_file(file, content_type, max_size)
