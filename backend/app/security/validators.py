"""
Input Validation & Sanitization for Finance Tracker

This module provides comprehensive input validation with:
- SQL injection prevention
- XSS prevention
- File upload validation
- Financial amount validation
- Date validation
- Email/phone sanitization

Security Level: BANK-GRADE
Compliance: OWASP, PCI-DSS
"""

import re
import html
import hashlib
import mimetypes
import logging
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any, Union, Tuple, Pattern
from dataclasses import dataclass
from enum import Enum
import unicodedata

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, field: str, message: str, code: str = "validation_error"):
        self.field = field
        self.message = message
        self.code = code
        super().__init__(f"{field}: {message}")


class ValidationType(Enum):
    """Types of validation."""
    REQUIRED = "required"
    FORMAT = "format"
    LENGTH = "length"
    RANGE = "range"
    PATTERN = "pattern"
    SECURITY = "security"


@dataclass
class ValidationResult:
    """Result of validation operation.
    
    Attributes:
        is_valid: Whether validation passed
        value: Sanitized/validated value
        errors: List of validation errors
    """
    is_valid: bool
    value: Any
    errors: List[str]


class SQLInjectionPatterns:
    """SQL injection detection patterns."""
    
    # Common SQL injection patterns
    PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE)\b)",
        r"(--|;|/\*|\*/|@@|@)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
        r"(\bOR\b\s*['\"].*['\"])",
        r"(\bUNION\b\s+\bSELECT\b)",
        r"(\bINTO\s+OUTFILE\b)",
        r"(\bLOAD_FILE\b)",
        r"(BENCHMARK\s*\()",
        r"(SLEEP\s*\()",
        r"(WAITFOR\s+DELAY)",
        r"(;.*--)",
        r"('\s*OR\s*')",
        r"(1\s*=\s*1)",
        r"(1\s*'\s*=\s*'\s*1)",
    ]
    
    COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PATTERNS]


class XSSPatterns:
    """XSS attack detection patterns."""
    
    # Common XSS patterns
    PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<form[^>]*>",
        r"<input[^>]*>",
        r"<img[^>]*onerror",
        r"<svg[^>]*onload",
        r"expression\s*\(",
        r"url\s*\(",
        r"<!--.*-->",
        r"&\{",
        r"<\s*meta",
        r"<\s*link",
        r"<\s*style",
        r"data:",
    ]
    
    COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PATTERNS]


class Sanitizer:
    """Input sanitization utility.
    
    Provides methods to sanitize various input types:
    - HTML escaping for XSS prevention
    - SQL parameter sanitization
    - Unicode normalization
    - Whitespace normalization
    
    Example:
        >>> sanitizer = Sanitizer()
        >>> safe_text = sanitizer.sanitize_html("<script>alert('xss')</script>")
        >>> safe_name = sanitizer.sanitize_name("John' OR '1'='1")
    """
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Escape HTML special characters.
        
        Args:
            text: Input text
            
        Returns:
            HTML-escaped text
        """
        return html.escape(text, quote=True)
    
    @staticmethod
    def strip_html(text: str) -> str:
        """Remove all HTML tags from text.
        
        Args:
            text: Input text with HTML
            
        Returns:
            Text with HTML tags removed
        """
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        clean = html.unescape(clean)
        return clean
    
    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Normalize Unicode text to NFC form.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        return unicodedata.normalize('NFC', text)
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in text.
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        return text.strip()
    
    @staticmethod
    def remove_control_characters(text: str) -> str:
        """Remove control characters from text.
        
        Args:
            text: Input text
            
        Returns:
            Text with control characters removed
        """
        return ''.join(
            char for char in text
            if unicodedata.category(char) != 'Cc' or char in '\n\r\t'
        )
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize a filename for safe storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        # Replace potentially dangerous characters
        filename = re.sub(r'[<>:"|?*]', '_', filename)
        
        # Prevent directory traversal
        filename = filename.lstrip('.')
        
        # Limit length
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if len(name) > 200:
            name = name[:200]
        
        return f"{name}.{ext}" if ext else name
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize an email address.
        
        Args:
            email: Email address
            
        Returns:
            Sanitized lowercase email
        """
        # Normalize and lowercase
        email = email.strip().lower()
        # Remove any potentially dangerous characters
        email = re.sub(r'[<>"\']', '', email)
        return email
    
    @staticmethod
    def sanitize_phone(phone: str) -> str:
        """Sanitize a phone number to digits only.
        
        Args:
            phone: Phone number
            
        Returns:
            Digits-only phone number with optional + prefix
        """
        # Keep + for international prefix
        has_plus = phone.startswith('+')
        # Extract digits only
        digits = re.sub(r'\D', '', phone)
        return f"+{digits}" if has_plus else digits


class InputValidator:
    """Comprehensive input validation for financial applications.
    
    Provides validation for:
    - SQL injection prevention
    - XSS attack prevention
    - File uploads
    - Financial amounts
    - Dates and times
    - Email and phone numbers
    
    Example:
        >>> validator = InputValidator()
        >>> result = validator.validate_amount("1000.50", currency="USD")
        >>> result = validator.validate_email("user@example.com")
        >>> result = validator.validate_file_upload(file_data, "statement.pdf")
    
    Security Considerations:
        - Always validate input at the boundary
        - Use parameterized queries in addition to validation
        - Implement defense in depth
    """
    
    # Email regex (RFC 5322 simplified)
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Phone regex (international format)
    PHONE_PATTERN = re.compile(
        r'^\+?[1-9]\d{1,14}$'
    )
    
    # UUID regex
    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    # Allowed file types for uploads
    ALLOWED_FILE_TYPES = {
        'document': {
            'application/pdf': ['.pdf'],
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'text/csv': ['.csv'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        },
        'image': {
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'image/gif': ['.gif'],
        },
    }
    
    # File size limits (in bytes)
    FILE_SIZE_LIMITS = {
        'document': 10 * 1024 * 1024,  # 10 MB
        'image': 5 * 1024 * 1024,       # 5 MB
    }
    
    # Currency configurations
    CURRENCY_CONFIG = {
        'USD': {'symbol': '$', 'decimals': 2, 'min': 0, 'max': 999999999.99},
        'EUR': {'symbol': '€', 'decimals': 2, 'min': 0, 'max': 999999999.99},
        'GBP': {'symbol': '£', 'decimals': 2, 'min': 0, 'max': 999999999.99},
        'INR': {'symbol': '₹', 'decimals': 2, 'min': 0, 'max': 9999999999.99},
        'JPY': {'symbol': '¥', 'decimals': 0, 'min': 0, 'max': 99999999999},
    }
    
    def __init__(self, strict_mode: bool = True):
        """Initialize validator.
        
        Args:
            strict_mode: If True, fail on any suspicious input
        """
        self._strict_mode = strict_mode
        self._sanitizer = Sanitizer()
    
    def check_sql_injection(self, value: str) -> Tuple[bool, Optional[str]]:
        """Check for SQL injection patterns.
        
        Args:
            value: Input string to check
            
        Returns:
            Tuple of (is_safe, detected_pattern)
        """
        for pattern in SQLInjectionPatterns.COMPILED_PATTERNS:
            match = pattern.search(value)
            if match:
                logger.warning(
                    "SQL injection pattern detected",
                    extra={"pattern": match.group(), "input_hash": hashlib.sha256(value.encode()).hexdigest()[:8]}
                )
                return False, match.group()
        return True, None
    
    def check_xss(self, value: str) -> Tuple[bool, Optional[str]]:
        """Check for XSS attack patterns.
        
        Args:
            value: Input string to check
            
        Returns:
            Tuple of (is_safe, detected_pattern)
        """
        for pattern in XSSPatterns.COMPILED_PATTERNS:
            match = pattern.search(value)
            if match:
                logger.warning(
                    "XSS pattern detected",
                    extra={"pattern": match.group(), "input_hash": hashlib.sha256(value.encode()).hexdigest()[:8]}
                )
                return False, match.group()
        return True, None
    
    def validate_string(
        self,
        value: Any,
        field_name: str = "field",
        min_length: int = 0,
        max_length: int = 10000,
        pattern: Optional[Pattern] = None,
        required: bool = True,
        allow_html: bool = False,
        check_injection: bool = True,
    ) -> ValidationResult:
        """Validate and sanitize a string input.
        
        Args:
            value: Input value
            field_name: Name of the field (for error messages)
            min_length: Minimum length
            max_length: Maximum length
            pattern: Optional regex pattern to match
            required: Whether field is required
            allow_html: Whether to allow HTML content
            check_injection: Whether to check for injection attacks
            
        Returns:
            ValidationResult with sanitized value
        """
        errors = []
        
        # Check required
        if value is None or (isinstance(value, str) and not value.strip()):
            if required:
                errors.append(f"{field_name} is required")
                return ValidationResult(False, None, errors)
            return ValidationResult(True, None, [])
        
        # Convert to string
        if not isinstance(value, str):
            value = str(value)
        
        # Normalize
        value = self._sanitizer.normalize_unicode(value)
        value = self._sanitizer.remove_control_characters(value)
        value = self._sanitizer.normalize_whitespace(value)
        
        # Length check
        if len(value) < min_length:
            errors.append(f"{field_name} must be at least {min_length} characters")
        if len(value) > max_length:
            errors.append(f"{field_name} must not exceed {max_length} characters")
        
        # Pattern check
        if pattern and not pattern.match(value):
            errors.append(f"{field_name} format is invalid")
        
        # Injection checks
        if check_injection:
            sql_safe, sql_pattern = self.check_sql_injection(value)
            if not sql_safe:
                errors.append(f"{field_name} contains invalid characters")
            
            xss_safe, xss_pattern = self.check_xss(value)
            if not xss_safe:
                errors.append(f"{field_name} contains invalid content")
        
        # Sanitize HTML
        if not allow_html:
            value = self._sanitizer.sanitize_html(value)
        
        return ValidationResult(len(errors) == 0, value, errors)
    
    def validate_email(
        self,
        value: str,
        field_name: str = "email",
        required: bool = True,
    ) -> ValidationResult:
        """Validate an email address.
        
        Args:
            value: Email address
            field_name: Field name for errors
            required: Whether field is required
            
        Returns:
            ValidationResult with sanitized email
        """
        errors = []
        
        if not value:
            if required:
                errors.append(f"{field_name} is required")
                return ValidationResult(False, None, errors)
            return ValidationResult(True, None, [])
        
        # Sanitize
        email = self._sanitizer.sanitize_email(value)
        
        # Validate format
        if not self.EMAIL_PATTERN.match(email):
            errors.append(f"{field_name} is not a valid email address")
        
        # Check for suspicious patterns
        if '..' in email or email.startswith('.') or email.endswith('.'):
            errors.append(f"{field_name} has invalid format")
        
        # Length check
        if len(email) > 254:  # RFC 5321
            errors.append(f"{field_name} is too long")
        
        return ValidationResult(len(errors) == 0, email, errors)
    
    def validate_phone(
        self,
        value: str,
        field_name: str = "phone",
        required: bool = True,
        country_code: Optional[str] = None,
    ) -> ValidationResult:
        """Validate a phone number.
        
        Args:
            value: Phone number
            field_name: Field name for errors
            required: Whether field is required
            country_code: Expected country code
            
        Returns:
            ValidationResult with sanitized phone
        """
        errors = []
        
        if not value:
            if required:
                errors.append(f"{field_name} is required")
                return ValidationResult(False, None, errors)
            return ValidationResult(True, None, [])
        
        # Sanitize
        phone = self._sanitizer.sanitize_phone(value)
        
        # Validate format
        if not self.PHONE_PATTERN.match(phone):
            errors.append(f"{field_name} is not a valid phone number")
        
        # Check country code if specified
        if country_code and not phone.startswith(f"+{country_code}"):
            errors.append(f"{field_name} must start with +{country_code}")
        
        return ValidationResult(len(errors) == 0, phone, errors)
    
    def validate_amount(
        self,
        value: Union[str, int, float, Decimal],
        field_name: str = "amount",
        currency: str = "USD",
        allow_negative: bool = False,
        allow_zero: bool = True,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
    ) -> ValidationResult:
        """Validate a financial amount.
        
        Args:
            value: Amount value
            field_name: Field name for errors
            currency: Currency code
            allow_negative: Allow negative amounts
            allow_zero: Allow zero amount
            min_amount: Minimum allowed amount
            max_amount: Maximum allowed amount
            
        Returns:
            ValidationResult with Decimal value
        """
        errors = []
        
        if value is None or value == '':
            errors.append(f"{field_name} is required")
            return ValidationResult(False, None, errors)
        
        # Get currency config
        currency_config = self.CURRENCY_CONFIG.get(currency, self.CURRENCY_CONFIG['USD'])
        
        # Convert to Decimal for precision
        try:
            if isinstance(value, str):
                # Remove currency symbols and commas
                clean_value = re.sub(r'[^\d.-]', '', value)
                amount = Decimal(clean_value)
            elif isinstance(value, float):
                # Use string conversion to avoid float precision issues
                amount = Decimal(str(value))
            elif isinstance(value, Decimal):
                amount = value
            else:
                amount = Decimal(value)
        except (InvalidOperation, ValueError):
            errors.append(f"{field_name} must be a valid number")
            return ValidationResult(False, None, errors)
        
        # Round to currency decimals
        quantize_str = '0.' + '0' * currency_config['decimals'] if currency_config['decimals'] > 0 else '0'
        amount = amount.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        
        # Check negative
        if amount < 0 and not allow_negative:
            errors.append(f"{field_name} cannot be negative")
        
        # Check zero
        if amount == 0 and not allow_zero:
            errors.append(f"{field_name} cannot be zero")
        
        # Check range
        effective_min = min_amount if min_amount is not None else Decimal(currency_config['min'])
        effective_max = max_amount if max_amount is not None else Decimal(str(currency_config['max']))
        
        if amount < effective_min:
            errors.append(f"{field_name} must be at least {effective_min}")
        if amount > effective_max:
            errors.append(f"{field_name} must not exceed {effective_max}")
        
        # Check for overflow (prevent integer overflow attacks)
        if abs(amount) > Decimal('9999999999999.99'):
            errors.append(f"{field_name} exceeds maximum allowed value")
        
        return ValidationResult(len(errors) == 0, amount, errors)
    
    def validate_date(
        self,
        value: Union[str, date, datetime],
        field_name: str = "date",
        required: bool = True,
        min_date: Optional[date] = None,
        max_date: Optional[date] = None,
        allow_future: bool = True,
        allow_past: bool = True,
    ) -> ValidationResult:
        """Validate a date value.
        
        Args:
            value: Date value
            field_name: Field name for errors
            required: Whether field is required
            min_date: Minimum allowed date
            max_date: Maximum allowed date
            allow_future: Allow future dates
            allow_past: Allow past dates
            
        Returns:
            ValidationResult with date value
        """
        errors = []
        
        if value is None or value == '':
            if required:
                errors.append(f"{field_name} is required")
                return ValidationResult(False, None, errors)
            return ValidationResult(True, None, [])
        
        # Parse date
        parsed_date = None
        if isinstance(value, datetime):
            parsed_date = value.date()
        elif isinstance(value, date):
            parsed_date = value
        elif isinstance(value, str):
            # Try common formats
            formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(value, fmt).date()
                    break
                except ValueError:
                    continue
            
            if parsed_date is None:
                errors.append(f"{field_name} has invalid date format")
                return ValidationResult(False, None, errors)
        
        today = date.today()
        
        # Check future/past
        if not allow_future and parsed_date > today:
            errors.append(f"{field_name} cannot be in the future")
        if not allow_past and parsed_date < today:
            errors.append(f"{field_name} cannot be in the past")
        
        # Check range
        if min_date and parsed_date < min_date:
            errors.append(f"{field_name} cannot be before {min_date}")
        if max_date and parsed_date > max_date:
            errors.append(f"{field_name} cannot be after {max_date}")
        
        return ValidationResult(len(errors) == 0, parsed_date, errors)
    
    def validate_file_upload(
        self,
        file_content: bytes,
        filename: str,
        file_type: str = "document",
        max_size: Optional[int] = None,
    ) -> ValidationResult:
        """Validate a file upload.
        
        Args:
            file_content: File binary content
            filename: Original filename
            file_type: Type of file (document/image)
            max_size: Maximum file size in bytes
            
        Returns:
            ValidationResult with sanitized filename
        """
        errors = []
        
        if not file_content:
            errors.append("File content is empty")
            return ValidationResult(False, None, errors)
        
        # Sanitize filename
        safe_filename = self._sanitizer.sanitize_filename(filename)
        
        # Check file size
        size_limit = max_size or self.FILE_SIZE_LIMITS.get(file_type, 10 * 1024 * 1024)
        if len(file_content) > size_limit:
            errors.append(f"File exceeds maximum size of {size_limit / (1024*1024):.1f} MB")
        
        # Get allowed types
        allowed_types = self.ALLOWED_FILE_TYPES.get(file_type, {})
        
        # Check extension
        ext = '.' + safe_filename.rsplit('.', 1)[-1].lower() if '.' in safe_filename else ''
        allowed_extensions = []
        for exts in allowed_types.values():
            allowed_extensions.extend(exts)
        
        if ext not in allowed_extensions:
            errors.append(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
        
        # Detect actual MIME type from content (magic bytes)
        detected_mime = self._detect_mime_type(file_content)
        
        if detected_mime not in allowed_types:
            errors.append(f"File content type not allowed: {detected_mime}")
        
        # Check for extension mismatch (potential attack)
        if detected_mime in allowed_types:
            expected_extensions = allowed_types[detected_mime]
            if ext not in expected_extensions:
                logger.warning(
                    "File extension mismatch",
                    extra={"filename": safe_filename, "detected_mime": detected_mime, "extension": ext}
                )
                errors.append("File extension does not match content type")
        
        # Check for embedded malicious content
        if self._check_malicious_content(file_content, detected_mime):
            errors.append("File contains potentially malicious content")
        
        return ValidationResult(len(errors) == 0, safe_filename, errors)
    
    def _detect_mime_type(self, content: bytes) -> str:
        """Detect MIME type from file content using magic bytes.
        
        Args:
            content: File content
            
        Returns:
            Detected MIME type
        """
        # Magic byte signatures
        signatures = {
            b'%PDF': 'application/pdf',
            b'\xff\xd8\xff': 'image/jpeg',
            b'\x89PNG\r\n\x1a\n': 'image/png',
            b'GIF87a': 'image/gif',
            b'GIF89a': 'image/gif',
            b'PK\x03\x04': 'application/zip',  # Also XLSX, DOCX
        }
        
        # Check for ZIP-based formats (XLSX, DOCX)
        if content[:4] == b'PK\x03\x04':
            if b'xl/' in content[:1000]:
                return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            if b'word/' in content[:1000]:
                return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        # Check signatures
        for signature, mime_type in signatures.items():
            if content.startswith(signature):
                return mime_type
        
        # Check for text/CSV
        try:
            content[:1000].decode('utf-8')
            if b',' in content[:1000]:
                return 'text/csv'
            return 'text/plain'
        except UnicodeDecodeError:
            pass
        
        return 'application/octet-stream'
    
    def _check_malicious_content(self, content: bytes, mime_type: str) -> bool:
        """Check for malicious content in uploaded files.
        
        Args:
            content: File content
            mime_type: Detected MIME type
            
        Returns:
            True if malicious content detected
        """
        # Check for script tags in any file
        content_str = content[:10000].decode('utf-8', errors='ignore').lower()
        
        dangerous_patterns = [
            '<script',
            'javascript:',
            'vbscript:',
            'data:text/html',
            'expression(',
            '<?php',
            '<%',
        ]
        
        for pattern in dangerous_patterns:
            if pattern in content_str:
                logger.warning(
                    "Malicious content detected in upload",
                    extra={"pattern": pattern, "mime_type": mime_type}
                )
                return True
        
        # Check for polyglot files (files that are valid in multiple formats)
        if mime_type.startswith('image/'):
            # Check for HTML/JS in image comments
            if b'<script' in content or b'javascript:' in content:
                return True
        
        return False
    
    def validate_uuid(
        self,
        value: str,
        field_name: str = "id",
        required: bool = True,
    ) -> ValidationResult:
        """Validate a UUID string.
        
        Args:
            value: UUID string
            field_name: Field name for errors
            required: Whether field is required
            
        Returns:
            ValidationResult with validated UUID
        """
        errors = []
        
        if not value:
            if required:
                errors.append(f"{field_name} is required")
                return ValidationResult(False, None, errors)
            return ValidationResult(True, None, [])
        
        if not self.UUID_PATTERN.match(value):
            errors.append(f"{field_name} is not a valid UUID")
        
        return ValidationResult(len(errors) == 0, value.lower(), errors)
    
    def validate_account_number(
        self,
        value: str,
        field_name: str = "account_number",
        required: bool = True,
    ) -> ValidationResult:
        """Validate a bank account number.
        
        Args:
            value: Account number
            field_name: Field name for errors
            required: Whether field is required
            
        Returns:
            ValidationResult with sanitized account number
        """
        errors = []
        
        if not value:
            if required:
                errors.append(f"{field_name} is required")
                return ValidationResult(False, None, errors)
            return ValidationResult(True, None, [])
        
        # Remove spaces and dashes
        account = re.sub(r'[\s-]', '', value)
        
        # Check for alphanumeric only
        if not account.isalnum():
            errors.append(f"{field_name} contains invalid characters")
        
        # Check length (varies by country, using US/IBAN range)
        if len(account) < 4 or len(account) > 34:
            errors.append(f"{field_name} has invalid length")
        
        # Check for injection
        sql_safe, _ = self.check_sql_injection(account)
        if not sql_safe:
            errors.append(f"{field_name} contains invalid characters")
        
        return ValidationResult(len(errors) == 0, account.upper(), errors)


# Validation guidelines
VALIDATION_GUIDELINES = """
## Input Validation Best Practices for Financial Applications

### Defense in Depth
1. Validate at every layer (client, API, service, database)
2. Use parameterized queries even with validated input
3. Implement output encoding for all user data
4. Log validation failures for security monitoring

### Financial Data Validation
1. Use Decimal for monetary amounts (never float)
2. Validate currency codes against ISO 4217
3. Check for reasonable amount ranges
4. Prevent negative amounts where inappropriate
5. Handle precision correctly per currency

### File Upload Security
1. Validate MIME type from content, not extension
2. Scan for malicious content
3. Store outside web root
4. Generate random filenames
5. Limit file size

### SQL Injection Prevention
1. Always use parameterized queries
2. Validate/sanitize as additional layer
3. Use ORM with proper configuration
4. Limit database user permissions

### XSS Prevention
1. HTML-encode all output
2. Use Content-Security-Policy headers
3. Set HttpOnly on cookies
4. Validate input types strictly
"""
