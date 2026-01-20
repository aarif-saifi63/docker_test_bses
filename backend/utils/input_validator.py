import re
from markupsafe import escape
import html

class InputValidator:

    # Allowed characters: English letters, numbers, space, hyphen, underscore, dot
    # AND Unicode characters for Hindi/Devanagari (\u0900-\u097F) and other languages
    SAFE_NAME_REGEX = r"^[A-Za-z0-9\u0900-\u097F _\.-\?]{1,100}$"
    SAFE_NAME_REGEX_FALL = r"^[A-Za-z0-9\u0900-\u097F _\.-]{1,1000}$"


    # Allowed characters for responses (more lenient, allows most text but blocks HTML/JS)
    # Supports Unicode for multilingual content
    SAFE_TEXT_REGEX = r"^[^<>]{1,5000}$"

    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Removes HTML tags & escapes unsafe characters
        """
        if not text:
            return ""

        # Escape HTML
        safe = escape(text)

        # Remove leftover tag-like structures
        safe = re.sub(r'<.*?>', '', safe)

        return safe

    @staticmethod
    def sanitize_html(text: str) -> str:
        """
        SECURITY: Sanitize text that may contain HTML/scripts
        - Strips all HTML tags
        - Escapes special characters
        - Removes JavaScript event handlers
        - Prevents XSS attacks
        """
        if not text:
            return ""

        # Convert to string if not already
        text = str(text)

        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove JavaScript event handlers (onclick, onerror, onload, etc.)
        text = re.sub(r'on\w+\s*=\s*["\']?[^"\']*["\']?', '', text, flags=re.IGNORECASE)

        # Remove javascript: protocol
        text = re.sub(r'javascript\s*:', '', text, flags=re.IGNORECASE)

        # Remove data: protocol (can be used for XSS)
        text = re.sub(r'data\s*:', '', text, flags=re.IGNORECASE)

        # Remove vbscript: protocol
        text = re.sub(r'vbscript\s*:', '', text, flags=re.IGNORECASE)

        # Escape remaining HTML entities
        text = html.escape(text)

        return text

    @staticmethod
    def validate_name(field_value: str, field_name: str = "name"):
        """
        Validates strings like ad_name, menu_name, etc.
        - Disallows HTML tags
        - Disallows JS
        - Disallows SQL keywords
        - Disallows special characters outside whitelist
        """
        if not field_value:
            return False, f"{field_name} is required"

        # Convert to string and strip whitespace
        field_value = str(field_value).strip()

        if not field_value:
            return False, f"{field_name} cannot be empty or whitespace only"

        # Check for HTML tags
        if '<' in field_value or '>' in field_value:
            return False, f"{field_name} contains HTML tags which are not allowed"

        # Validate against whitelist pattern (supports English & Hindi/Devanagari)
        if not re.match(InputValidator.SAFE_NAME_REGEX, field_value):
            return False, (
                f"Invalid {field_name}. Only alphabets (English/Hindi), numbers, space, dot, "
                f"hyphen and underscore are allowed (max 100 characters)."
            )

        # Block common attack keywords and patterns
        forbidden_keywords = [
            "script", "alert(", "onerror", "onload", "onclick", "onmouseover",
            "onfocus", "onblur", "javascript:", "vbscript:", "data:",
            "<iframe", "<embed", "<object", "<form",
            "drop table", "insert into", "update ", "delete from", "truncate",
            "exec(", "eval(", "expression(", "import(", "\\x", "&#"
        ]

        field_lower = field_value.lower()
        for kw in forbidden_keywords:
            if kw.lower() in field_lower:
                return False, f"{field_name} contains forbidden keyword or pattern"

        return True, "OK"

    @staticmethod
    def validate_text_content(field_value: str, field_name: str = "content", max_length: int = 5000):
        """
        SECURITY: Validate longer text fields (like utter responses, descriptions)
        - Allows most characters but blocks HTML/script tags
        - Blocks JavaScript event handlers
        - Blocks dangerous protocols
        - More lenient than validate_name but still secure

        Args:
            field_value: The text to validate
            field_name: Name of the field for error messages
            max_length: Maximum allowed length (default 5000)

        Returns:
            tuple: (is_valid: bool, message: str)
        """
        if not field_value:
            return False, f"{field_name} is required"

        # Convert to string and strip
        field_value = str(field_value).strip()

        if not field_value:
            return False, f"{field_name} cannot be empty or whitespace only"

        # Check length
        if len(field_value) > max_length:
            return False, f"{field_name} exceeds maximum length of {max_length} characters"

        # Block HTML tags
        if '<' in field_value or '>' in field_value:
            return False, f"{field_name} contains HTML tags which are not allowed"

        # Block JavaScript event handlers
        event_handlers = r'on(load|click|error|focus|blur|change|submit|mouseover|mouseout|keypress|keydown|keyup)\s*='
        if re.search(event_handlers, field_value, re.IGNORECASE):
            return False, f"{field_name} contains JavaScript event handlers which are not allowed"

        # Block dangerous protocols
        dangerous_protocols = [
            r'javascript\s*:',
            r'data\s*:',
            r'vbscript\s*:',
            r'file\s*:',
            r'about\s*:'
        ]

        for protocol in dangerous_protocols:
            if re.search(protocol, field_value, re.IGNORECASE):
                return False, f"{field_name} contains dangerous protocol which is not allowed"

        # Block script-related keywords
        script_keywords = [
            r'<script[^>]*>',
            r'</script>',
            r'<iframe[^>]*>',
            r'<embed[^>]*>',
            r'<object[^>]*>',
            r'eval\s*\(',
            r'exec\s*\(',
            r'expression\s*\(',
            r'import\s*\(',
            r'document\.',
            r'window\.',
            r'alert\s*\(',
            r'confirm\s*\(',
            r'prompt\s*\('
        ]

        for keyword in script_keywords:
            if re.search(keyword, field_value, re.IGNORECASE):
                return False, f"{field_name} contains script-related content which is not allowed"

        # Block SQL injection patterns
        sql_patterns = [
            r'\b(drop|truncate|delete|insert|update)\s+(table|into|from)\b',
            r';\s*drop\s+',
            r'--\s*$',
            r'/\*.*\*/',
            r'union\s+select',
            r'or\s+1\s*=\s*1',
            r'and\s+1\s*=\s*1'
        ]

        for pattern in sql_patterns:
            if re.search(pattern, field_value, re.IGNORECASE):
                return False, f"{field_name} contains SQL injection patterns which are not allowed"

        return True, "OK"



    @staticmethod
    def validate_fallback(field_value: str, field_name: str = "name"):
        """
        Validates strings like ad_name, menu_name, etc.
        - Disallows HTML tags
        - Disallows JS
        - Disallows SQL keywords
        - Disallows special characters outside whitelist
        """
        if not field_value:
            return False, f"{field_name} is required"

        # Convert to string and strip whitespace
        field_value = str(field_value).strip()

        if not field_value:
            return False, f"{field_name} cannot be empty or whitespace only"

        # Check for HTML tags
        if '<' in field_value or '>' in field_value:
            return False, f"{field_name} contains HTML tags which are not allowed"

        # Validate against whitelist pattern (supports English & Hindi/Devanagari)
        # if not re.match(InputValidator.SAFE_NAME_REGEX_FALL, field_value):
        #     return False, (
        #         f"Invalid {field_name}. Only alphabets (English/Hindi), numbers, space, dot, "
        #         f"hyphen and underscore are allowed (max 100 characters)."
        #     )

        # Block common attack keywords and patterns
        forbidden_keywords = [
            "script", "alert(", "onerror", "onload", "onclick", "onmouseover",
            "onfocus", "onblur", "javascript:", "vbscript:", "data:",
            "<iframe", "<embed", "<object", "<form",
            "drop table", "insert into", "update ", "delete from", "truncate",
            "exec(", "eval(", "expression(", "import(", "\\x", "&#", "svg", "php"
        ]

        field_lower = field_value.lower()
        for kw in forbidden_keywords:
            if kw.lower() in field_lower:
                return False, f"{field_name} contains forbidden keyword or pattern"

        return True, "OK"

    @staticmethod
    def validate_no_csv_injection(field_value: str, field_name: str = "field"):
        """
        SECURITY: Validates input to prevent CSV/Formula Injection attacks

        CSV injection occurs when special characters at the beginning of input
        can be interpreted as formulas by spreadsheet applications (Excel, Google Sheets, etc.)

        This method REJECTS any input that could be used for CSV injection.

        Dangerous patterns:
        - Starts with: = + - @ (formula characters)
        - Contains: \t (tab), \r (carriage return)
        - DDE attack patterns with pipe character: =cmd|'/c calc'!A1

        Args:
            field_value: The text to validate
            field_name: Name of the field for error messages

        Returns:
            tuple: (is_valid: bool, message: str)

        Example:
            validate_no_csv_injection("=1+1", "input") -> (False, "input cannot start with = (CSV injection risk)")
            validate_no_csv_injection("normal text", "input") -> (True, "OK")
            validate_no_csv_injection("-5", "amount") -> (False, "amount cannot start with - (CSV injection risk)")
        """
        if not field_value:
            return True, "OK"

        # Convert to string and check both original and stripped versions
        field_value = str(field_value)
        stripped_value = field_value.lstrip()

        # Define dangerous prefixes that can trigger formula execution
        dangerous_prefixes = {
            '=': 'equals sign',
            '+': 'plus sign',
            '-': 'minus/hyphen',
            '@': 'at symbol'
        }

        # Check if field starts with dangerous character (after stripping whitespace)
        if stripped_value:
            first_char = stripped_value[0]
            if first_char in dangerous_prefixes:
                prefix_name = dangerous_prefixes[first_char]
                return False, f"{field_name} cannot start with {first_char} ({prefix_name}) - CSV injection risk"

        # Check for tab characters (used in CSV injection)
        if '\t' in field_value:
            return False, f"{field_name} cannot contain tab characters - CSV injection risk"

        # Check for carriage return (used in CSV injection)
        if '\r' in field_value:
            return False, f"{field_name} cannot contain carriage return characters - CSV injection risk"

        # Check for DDE (Dynamic Data Exchange) attack patterns
        # Format: =cmd|'/c calc'!A1 or @SUM(1+1)*cmd|'/c calc'!A1
        if '|' in field_value:
            # Check if there are any formula indicators combined with pipe
            has_formula_chars = any(char in field_value for char in ['=', '+', '@'])
            if has_formula_chars:
                return False, f"{field_name} contains potential DDE attack pattern (pipe with formula characters)"

        return True, "OK"

