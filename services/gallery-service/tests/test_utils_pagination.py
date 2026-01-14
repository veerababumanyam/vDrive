"""Tests for cursor-based pagination utilities."""

import base64
import json

from src.app.utils.pagination import decode_cursor, encode_cursor


class TestEncodeCursor:
    """Test cursor encoding."""

    def test_encode_cursor_valid(self):
        """Test encoding a valid cursor."""
        created_at = "2024-01-15T10:30:00Z"
        record_id = "00000000-0000-0000-0000-000000000123"

        cursor = encode_cursor(created_at, record_id)

        # Should return base64-encoded string
        assert isinstance(cursor, str)
        assert len(cursor) > 0

        # Should be valid base64
        decoded_bytes = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        decoded_str = decoded_bytes.decode("utf-8")
        data = json.loads(decoded_str)

        assert data["created_at"] == created_at
        assert data["id"] == record_id

    def test_encode_cursor_with_special_characters(self):
        """Test encoding cursor with special characters in timestamp."""
        created_at = "2024-01-15T10:30:00.123456+00:00"
        record_id = "abcdef12-3456-7890-abcd-ef1234567890"

        cursor = encode_cursor(created_at, record_id)

        # Should handle special characters in ISO timestamp
        assert isinstance(cursor, str)
        decoded_bytes = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        decoded_str = decoded_bytes.decode("utf-8")
        data = json.loads(decoded_str)

        assert data["created_at"] == created_at
        assert data["id"] == record_id

    def test_encode_cursor_url_safe(self):
        """Test that encoded cursor is URL-safe."""
        created_at = "2024-01-15T10:30:00Z"
        record_id = "00000000-0000-0000-0000-000000000123"

        cursor = encode_cursor(created_at, record_id)

        # Should not contain characters that need URL encoding
        assert "+" not in cursor
        assert "/" not in cursor
        # URL-safe base64 uses - and _ instead


class TestDecodeCursor:
    """Test cursor decoding."""

    def test_decode_cursor_valid(self):
        """Test decoding a valid cursor."""
        created_at = "2024-01-15T10:30:00Z"
        record_id = "00000000-0000-0000-0000-000000000123"

        # Encode first
        cursor = encode_cursor(created_at, record_id)

        # Decode
        result = decode_cursor(cursor)

        assert result is not None
        decoded_created_at, decoded_id = result
        assert decoded_created_at == created_at
        assert decoded_id == record_id

    def test_decode_cursor_invalid_base64(self):
        """Test decoding invalid base64 returns None."""
        invalid_cursor = "not-valid-base64!!!"

        result = decode_cursor(invalid_cursor)

        assert result is None

    def test_decode_cursor_invalid_json(self):
        """Test decoding cursor with invalid JSON returns None."""
        # Valid base64 but not valid JSON
        invalid_json = base64.urlsafe_b64encode(b"not json").decode("utf-8")

        result = decode_cursor(invalid_json)

        assert result is None

    def test_decode_cursor_missing_fields(self):
        """Test decoding cursor with missing required fields returns None."""
        # Valid JSON but missing required fields
        incomplete_data = {"created_at": "2024-01-15T10:30:00Z"}  # Missing 'id'
        json_str = json.dumps(incomplete_data)
        cursor = base64.urlsafe_b64encode(json_str.encode("utf-8")).decode("utf-8")

        result = decode_cursor(cursor)

        assert result is None

    def test_decode_cursor_empty_string(self):
        """Test decoding empty string returns None."""
        result = decode_cursor("")

        assert result is None

    def test_encode_decode_roundtrip(self):
        """Test that encode->decode roundtrip preserves data."""
        test_cases = [
            ("2024-01-15T10:30:00Z", "00000000-0000-0000-0000-000000000123"),
            (
                "2024-12-31T23:59:59.999999Z",
                "ffffffff-ffff-ffff-ffff-ffffffffffff",
            ),
            ("2024-01-01T00:00:00+00:00", "12345678-90ab-cdef-1234-567890abcdef"),
        ]

        for created_at, record_id in test_cases:
            cursor = encode_cursor(created_at, record_id)
            decoded = decode_cursor(cursor)

            assert decoded is not None
            decoded_created_at, decoded_id = decoded
            assert decoded_created_at == created_at
            assert decoded_id == record_id
