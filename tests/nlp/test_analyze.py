"""Tests for sentiment analysis utilities.

NOTE: These tests mock pysentimiento to avoid downloading models during CI.
For integration tests with actual models, use the analysis notebooks.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestAnalyzeSentiment:
    """Tests for the analyze_sentiment function."""

    @patch("nlp.analyze.get_analyzer")
    def test_returns_list_of_dicts(self, mock_get: MagicMock) -> None:
        """Should return a list of dicts with label and probas."""
        mock_result = MagicMock()
        mock_result.output = "POS"
        mock_result.probas = {"POS": 0.8, "NEG": 0.1, "NEU": 0.1}

        mock_analyzer = MagicMock()
        mock_analyzer.predict.return_value = mock_result
        mock_get.return_value = mock_analyzer

        from nlp.analyze import analyze_sentiment

        results = analyze_sentiment(["Texto positivo"])

        assert len(results) == 1
        assert results[0]["label"] == "POS"
        assert "probas" in results[0]

    @patch("nlp.analyze.get_analyzer")
    def test_handles_multiple_texts(self, mock_get: MagicMock) -> None:
        """Should process multiple texts."""
        mock_result = MagicMock()
        mock_result.output = "NEU"
        mock_result.probas = {"POS": 0.3, "NEG": 0.3, "NEU": 0.4}

        mock_analyzer = MagicMock()
        mock_analyzer.predict.return_value = mock_result
        mock_get.return_value = mock_analyzer

        from nlp.analyze import analyze_sentiment

        texts = ["Texto uno", "Texto dos", "Texto tres"]
        results = analyze_sentiment(texts)

        assert len(results) == 3

    @patch("nlp.analyze.get_analyzer")
    def test_empty_input(self, mock_get: MagicMock) -> None:
        """Should handle empty input list."""
        mock_get.return_value = MagicMock()

        from nlp.analyze import analyze_sentiment

        results = analyze_sentiment([])

        assert results == []
