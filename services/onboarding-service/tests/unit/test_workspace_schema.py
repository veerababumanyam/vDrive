"""
Unit tests for workspace schema validation.
"""

import pytest
from pydantic import ValidationError

from src.app.schemas.workspace import WorkspaceCreateRequest


class TestWorkspaceCreateRequest:
    """Tests for workspace creation request validation."""

    def test_valid_workspace(self):
        """Valid workspace data should pass validation."""
        data = {
            "name": "Lumina Photography Studio",
            "slug": "lumina-photography-studio",
            "business_type": "wedding",
        }
        request = WorkspaceCreateRequest(**data)

        assert request.name == "Lumina Photography Studio"
        assert request.slug == "lumina-photography-studio"
        assert request.business_type.value == "wedding"

    def test_slug_lowercase_conversion(self):
        """Slug should be converted to lowercase."""
        data = {
            "name": "Test Studio",
            "slug": "My-STUDIO",
            "business_type": "portrait",
        }
        request = WorkspaceCreateRequest(**data)

        assert request.slug == "my-studio"

    def test_slug_invalid_format_uppercase(self):
        """Slug with consecutive hyphens should fail."""
        data = {
            "name": "Test Studio",
            "slug": "my--studio",  # Consecutive hyphens
            "business_type": "portrait",
        }

        with pytest.raises(ValidationError) as exc_info:
            WorkspaceCreateRequest(**data)

        assert "slug" in str(exc_info.value).lower()

    def test_slug_invalid_leading_hyphen(self):
        """Slug starting with hyphen should fail."""
        data = {
            "name": "Test Studio",
            "slug": "-my-studio",
            "business_type": "portrait",
        }

        with pytest.raises(ValidationError) as exc_info:
            WorkspaceCreateRequest(**data)

        assert "slug" in str(exc_info.value).lower()

    def test_slug_invalid_trailing_hyphen(self):
        """Slug ending with hyphen should fail."""
        data = {
            "name": "Test Studio",
            "slug": "my-studio-",
            "business_type": "portrait",
        }

        with pytest.raises(ValidationError) as exc_info:
            WorkspaceCreateRequest(**data)

        assert "slug" in str(exc_info.value).lower()

    def test_slug_with_underscores(self):
        """Slug with underscores should fail."""
        data = {
            "name": "Test Studio",
            "slug": "my_studio",
            "business_type": "portrait",
        }

        with pytest.raises(ValidationError) as exc_info:
            WorkspaceCreateRequest(**data)

        assert "slug" in str(exc_info.value).lower()

    def test_slug_with_spaces(self):
        """Slug with spaces should fail."""
        data = {
            "name": "Test Studio",
            "slug": "my studio",
            "business_type": "portrait",
        }

        with pytest.raises(ValidationError) as exc_info:
            WorkspaceCreateRequest(**data)

        assert "slug" in str(exc_info.value).lower()

    def test_brand_color_valid_hex(self):
        """Valid hex color should pass."""
        data = {
            "name": "Test Studio",
            "slug": "test-studio",
            "business_type": "wedding",
            "brand_color": "#4A90D9",
        }
        request = WorkspaceCreateRequest(**data)

        assert request.brand_color == "#4A90D9"

    def test_brand_color_lowercase_converted(self):
        """Lowercase hex color should be converted to uppercase."""
        data = {
            "name": "Test Studio",
            "slug": "test-studio",
            "business_type": "wedding",
            "brand_color": "#4a90d9",
        }
        request = WorkspaceCreateRequest(**data)

        assert request.brand_color == "#4A90D9"

    def test_brand_color_invalid_format(self):
        """Invalid hex color format should fail."""
        invalid_colors = [
            "4A90D9",  # Missing #
            "#4A90D",  # Too short
            "#4A90D9FF",  # Too long
            "#GGGGGG",  # Invalid characters
            "red",  # Named color
        ]

        for color in invalid_colors:
            data = {
                "name": "Test Studio",
                "slug": "test-studio",
                "business_type": "wedding",
                "brand_color": color,
            }

            with pytest.raises(ValidationError):
                WorkspaceCreateRequest(**data)

    def test_currency_uppercase_conversion(self):
        """Currency should be converted to uppercase."""
        data = {
            "name": "Test Studio",
            "slug": "test-studio",
            "business_type": "wedding",
            "currency": "usd",
        }
        request = WorkspaceCreateRequest(**data)

        assert request.currency == "USD"

    def test_default_values(self):
        """Default values should be set correctly."""
        data = {
            "name": "Test Studio",
            "slug": "test-studio",
            "business_type": "wedding",
        }
        request = WorkspaceCreateRequest(**data)

        assert request.currency == "USD"
        assert request.timezone == "UTC"
        assert request.date_format == "YYYY-MM-DD"
        assert request.brand_color is None
        assert request.logo_url is None

    def test_invalid_business_type(self):
        """Invalid business type should fail."""
        data = {
            "name": "Test Studio",
            "slug": "test-studio",
            "business_type": "invalid_type",
        }

        with pytest.raises(ValidationError) as exc_info:
            WorkspaceCreateRequest(**data)

        assert "business_type" in str(exc_info.value).lower()

    def test_all_business_types_valid(self):
        """All valid business types should pass."""
        valid_types = ["wedding", "portrait", "event", "corporate", "other"]

        for business_type in valid_types:
            data = {
                "name": "Test Studio",
                "slug": "test-studio",
                "business_type": business_type,
            }
            request = WorkspaceCreateRequest(**data)
            assert request.business_type.value == business_type
