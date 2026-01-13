"""
Unit tests for workspace service.
"""

import pytest

from src.app.services.workspace_service import WorkspaceService


class TestSlugGeneration:
    """Tests for slug generation from business names."""

    @pytest.fixture
    def service(self):
        """Create workspace service without database."""
        # Pass None for db since we're only testing slug generation
        return WorkspaceService(db=None)

    def test_generate_slug_simple(self, service):
        """Simple name should generate clean slug."""
        slug = service.generate_slug("Lumina Studios")

        assert slug == "lumina-studios"

    def test_generate_slug_lowercase(self, service):
        """Slug should be lowercase."""
        slug = service.generate_slug("LUMINA STUDIOS")

        assert slug == "lumina-studios"

    def test_generate_slug_removes_special_chars(self, service):
        """Special characters should be replaced with hyphens."""
        slug = service.generate_slug("John's Photography & Co.")

        assert slug == "john-s-photography-co"

    def test_generate_slug_unicode(self, service):
        """Unicode characters should be transliterated."""
        slug = service.generate_slug("Café Photo München")

        assert slug == "cafe-photo-munchen"

    def test_generate_slug_multiple_spaces(self, service):
        """Multiple spaces should become single hyphen."""
        slug = service.generate_slug("Lumina    Studios")

        assert slug == "lumina-studios"

    def test_generate_slug_no_leading_hyphen(self, service):
        """Slug should not have leading hyphen."""
        slug = service.generate_slug("   Lumina Studios")

        assert not slug.startswith("-")

    def test_generate_slug_no_trailing_hyphen(self, service):
        """Slug should not have trailing hyphen."""
        slug = service.generate_slug("Lumina Studios   ")

        assert not slug.endswith("-")

    def test_generate_slug_max_length(self, service):
        """Slug should be truncated to 50 characters."""
        long_name = "A" * 100 + " Photography Studio"
        slug = service.generate_slug(long_name)

        assert len(slug) <= 50

    def test_generate_slug_truncate_at_hyphen(self, service):
        """Long slug should truncate at hyphen boundary if possible."""
        name = "This Is A Very Long Photography Studio Name That Should Be Truncated"
        slug = service.generate_slug(name)

        assert len(slug) <= 50
        # Should not end with a partial word
        assert slug.endswith("that")

    def test_generate_slug_numbers(self, service):
        """Numbers should be preserved."""
        slug = service.generate_slug("Studio 2024 Photography")

        assert slug == "studio-2024-photography"

    def test_generate_slug_consecutive_specials(self, service):
        """Consecutive special chars should become single hyphen."""
        slug = service.generate_slug("Photo -- Studio & Co.")

        assert "--" not in slug
        assert slug == "photo-studio-co"

    def test_generate_slug_emoji(self, service):
        """Emojis should be removed."""
        slug = service.generate_slug("Photo Studio ✨📸")

        assert "✨" not in slug
        assert "📸" not in slug
        assert slug == "photo-studio"

    def test_generate_slug_only_special_chars(self, service):
        """Name with only special chars should return empty or minimal slug."""
        slug = service.generate_slug("### !!!")

        # Should be empty after all special chars removed
        assert slug == ""

    def test_generate_slug_accented_characters(self, service):
        """Accented characters should be transliterated."""
        slug = service.generate_slug("Étoile Photographié")

        assert slug == "etoile-photographie"

    def test_generate_slug_chinese_characters(self, service):
        """Chinese characters should be transliterated."""
        slug = service.generate_slug("北京摄影工作室")

        # Transliterated to pinyin-like representation
        assert len(slug) > 0
        assert all(c.isalnum() or c == "-" for c in slug)

    def test_generate_slug_mixed_unicode(self, service):
        """Mixed unicode should be handled."""
        slug = service.generate_slug("Café München 東京 Photo")

        # Should contain transliterated versions
        assert "cafe" in slug
        assert "munchen" in slug


class TestSlugValidation:
    """Tests for slug format validation."""

    def test_valid_slug_format(self):
        """Valid slugs should match expected pattern."""
        valid_slugs = [
            "lumina-studios",
            "photo-studio-123",
            "my-photography",
            "studio",
            "a1",
        ]

        import re
        pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"

        for slug in valid_slugs:
            assert re.match(pattern, slug), f"'{slug}' should be valid"

    def test_invalid_slug_format(self):
        """Invalid slugs should not match pattern."""
        invalid_slugs = [
            "Lumina-Studios",  # Uppercase
            "-lumina-studios",  # Leading hyphen
            "lumina-studios-",  # Trailing hyphen
            "lumina--studios",  # Double hyphen
            "lumina studios",  # Space
            "lumina_studios",  # Underscore
        ]

        import re
        pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"

        for slug in invalid_slugs:
            assert not re.match(pattern, slug), f"'{slug}' should be invalid"
