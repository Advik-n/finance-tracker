"""
Utility Helpers

Common utility functions used throughout the application.
"""

import re
import hashlib
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID


def generate_slug(text: str) -> str:
    """
    Generate URL-safe slug from text.
    
    Args:
        text: Text to slugify
        
    Returns:
        Lowercase slug with hyphens
    """
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)
    
    # Remove non-alphanumeric characters (except hyphens)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    
    # Remove multiple consecutive hyphens
    slug = re.sub(r"-+", "-", slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    
    return slug


def hash_string(text: str) -> str:
    """
    Generate SHA-256 hash of a string.
    
    Args:
        text: Text to hash
        
    Returns:
        Hex-encoded hash string
    """
    return hashlib.sha256(text.encode()).hexdigest()


def format_currency(
    amount: Decimal,
    currency: str = "USD",
    locale: str = "en_US",
) -> str:
    """
    Format decimal amount as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency code
        locale: Locale for formatting
        
    Returns:
        Formatted currency string
    """
    symbol = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "INR": "₹",
    }.get(currency, currency)
    
    if currency == "JPY":
        return f"{symbol}{amount:,.0f}"
    
    return f"{symbol}{amount:,.2f}"


def parse_date_range(
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> tuple:
    """
    Parse date range strings with defaults.
    
    Args:
        start: Start date string (YYYY-MM-DD)
        end: End date string (YYYY-MM-DD)
        
    Returns:
        Tuple of (start_date, end_date)
    """
    today = date.today()
    
    if end:
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    else:
        end_date = today
    
    if start:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
    else:
        start_date = date(today.year, today.month, 1)
    
    return start_date, end_date


def mask_email(email: str) -> str:
    """
    Mask email address for privacy.
    
    Args:
        email: Email address to mask
        
    Returns:
        Masked email (e.g., "j***@example.com")
    """
    if "@" not in email:
        return email
    
    local, domain = email.rsplit("@", 1)
    
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    
    return f"{masked_local}@{domain}"


def paginate(
    items: list,
    page: int = 1,
    limit: int = 50,
) -> dict:
    """
    Paginate a list of items.
    
    Args:
        items: List to paginate
        page: Page number (1-indexed)
        limit: Items per page
        
    Returns:
        Dict with paginated items and metadata
    """
    total = len(items)
    pages = (total + limit - 1) // limit
    
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }


def safe_uuid(value: Any) -> Optional[UUID]:
    """
    Safely convert value to UUID.
    
    Args:
        value: Value to convert
        
    Returns:
        UUID or None if invalid
    """
    if value is None:
        return None
    
    if isinstance(value, UUID):
        return value
    
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def calculate_percentage_change(
    old_value: Decimal,
    new_value: Decimal,
) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        old_value: Previous value
        new_value: Current value
        
    Returns:
        Percentage change
    """
    if old_value == 0:
        if new_value > 0:
            return 100.0
        return 0.0
    
    change = (new_value - old_value) / old_value * 100
    return round(float(change), 2)


def truncate_string(text: str, max_length: int = 100) -> str:
    """
    Truncate string to maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        
    Returns:
        Truncated string with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."
