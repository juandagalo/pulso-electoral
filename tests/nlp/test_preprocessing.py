"""Tests for text preprocessing utilities."""

from __future__ import annotations

from nlp.preprocessing import clean_text, normalize_colombian_text


class TestCleanText:
    """Tests for the clean_text function."""

    def test_removes_urls(self) -> None:
        """Should remove HTTP and HTTPS URLs."""
        text = "Check this https://example.com for more info"
        result = clean_text(text)
        assert "https://example.com" not in result
        assert "Check this" in result

    def test_removes_mentions(self) -> None:
        """Should remove @mentions."""
        text = "@petro dice que va a reformar todo"
        result = clean_text(text)
        assert "@petro" not in result
        assert "dice que va a reformar todo" in result

    def test_removes_html_tags(self) -> None:
        """Should remove HTML tags."""
        text = "<p>Noticias de <b>Colombia</b></p>"
        result = clean_text(text)
        assert "<p>" not in result
        assert "Noticias de Colombia" in result

    def test_normalizes_whitespace(self) -> None:
        """Should collapse multiple spaces into one."""
        text = "Petro   dice    que   va"
        result = clean_text(text)
        assert result == "Petro dice que va"

    def test_strips_whitespace(self) -> None:
        """Should strip leading and trailing whitespace."""
        text = "  Noticias de Colombia  "
        result = clean_text(text)
        assert result == "Noticias de Colombia"

    def test_empty_string(self) -> None:
        """Should handle empty strings."""
        assert clean_text("") == ""


class TestNormalizeColombianText:
    """Tests for the normalize_colombian_text function."""

    def test_preserves_normal_text(self) -> None:
        """Should not modify text without Colombian slang."""
        text = "Las elecciones seran en marzo de 2026"
        # Even if slang map is empty or not loaded, normal text should pass through
        result = normalize_colombian_text(text)
        assert "elecciones" in result

    def test_returns_string(self) -> None:
        """Should always return a string."""
        result = normalize_colombian_text("Test text")
        assert isinstance(result, str)

    def test_handles_empty_string(self) -> None:
        """Should handle empty strings gracefully."""
        result = normalize_colombian_text("")
        assert result == ""
