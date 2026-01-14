"""Validation utilities for email and PIN formats"""

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validate email format using RFC 5322 simplified regex.

    Args:
        email: Email address to validate

    Returns:
        True if valid email format, False otherwise
    """
    # RFC 5322 simplified pattern
    pattern = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    return bool(re.match(pattern, email))


def validate_pin(pin: str) -> tuple[bool, Optional[str]]:
    """
    Validate PIN format (4-6 digits).

    Args:
        pin: PIN string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not pin:
        return False, "PIN is required"

    if not pin.isdigit():
        return False, "PIN must contain only digits"

    if len(pin) < 4:
        return False, "PIN must be at least 4 digits"

    if len(pin) > 6:
        return False, "PIN must be at most 6 digits"

    return True, None


def validate_hex_color(color: str) -> bool:
    """
    Validate hex color format (#RRGGBB or #RGB).

    Args:
        color: Hex color string

    Returns:
        True if valid hex color, False otherwise
    """
    if not color:
        return False
    pattern = r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
    return bool(re.match(pattern, color))
