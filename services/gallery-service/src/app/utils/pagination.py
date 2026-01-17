"""Cursor-based pagination utilities for O(1) performance"""

import base64
import json
from typing import Optional, Tuple


def encode_cursor(created_at: str, id: str) -> str:
    """
    Encode pagination cursor from timestamp and ID.

    Args:
        created_at: ISO timestamp string
        id: Record UUID string

    Returns:
        Base64-encoded cursor string
    """
    cursor_data = {"created_at": created_at, "id": id}
    json_str = json.dumps(cursor_data)
    return base64.urlsafe_b64encode(json_str.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor: str) -> Optional[Tuple[str, str]]:
    """
    Decode pagination cursor to timestamp and ID.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Tuple of (created_at, id) or None if invalid
    """
    try:
        json_str = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        cursor_data = json.loads(json_str)
        return cursor_data["created_at"], cursor_data["id"]
    except Exception:
        return None
