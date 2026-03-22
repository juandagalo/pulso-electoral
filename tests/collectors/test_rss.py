"""Tests for RSS feed collection utilities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from collectors.rss import collect_feeds, collect_feeds_from_config


class TestCollectFeeds:
    """Tests for the collect_feeds function."""

    @patch("collectors.rss.feedparser.parse")
    @patch("collectors.rss.time.sleep")
    def test_collect_feeds_returns_articles(
        self, mock_sleep: MagicMock, mock_parse: MagicMock
    ) -> None:
        """Collect feeds should return a list of article dictionaries."""
        mock_parse.return_value = MagicMock(
            entries=[
                MagicMock(
                    **{
                        "get.side_effect": lambda key, default="": {
                            "title": "Test Article",
                            "link": "https://example.com/article",
                            "published": "2026-03-22",
                            "summary": "Test summary",
                            "author": "Test Author",
                            "tags": [],
                        }.get(key, default),
                    }
                )
            ],
            feed=MagicMock(
                **{
                    "get.side_effect": lambda key, default="": {
                        "title": "Test Feed",
                    }.get(key, default),
                }
            ),
        )

        results = collect_feeds(["https://example.com/rss"], delay=0)

        assert len(results) == 1
        assert results[0]["title"] == "Test Article"
        assert results[0]["source"] == "Test Feed"

    @patch("collectors.rss.feedparser.parse")
    @patch("collectors.rss.time.sleep")
    def test_collect_feeds_empty_feed(
        self, mock_sleep: MagicMock, mock_parse: MagicMock
    ) -> None:
        """Collect feeds should handle empty feeds gracefully."""
        mock_parse.return_value = MagicMock(
            entries=[],
            feed=MagicMock(**{"get.return_value": "Empty Feed"}),
        )

        results = collect_feeds(["https://example.com/empty"], delay=0)

        assert results == []

    @patch("collectors.rss.feedparser.parse")
    @patch("collectors.rss.time.sleep")
    def test_collect_feeds_multiple_urls(
        self, mock_sleep: MagicMock, mock_parse: MagicMock
    ) -> None:
        """Collect feeds should process multiple URLs."""
        mock_parse.return_value = MagicMock(
            entries=[],
            feed=MagicMock(**{"get.return_value": "Feed"}),
        )

        collect_feeds(["https://a.com/rss", "https://b.com/rss"], delay=0)

        assert mock_parse.call_count == 2


class TestCollectFeedsFromConfig:
    """Tests for the collect_feeds_from_config function."""

    @patch("collectors.rss.feedparser.parse")
    @patch("collectors.rss.time.sleep")
    def test_uses_config_name_as_source(
        self, mock_sleep: MagicMock, mock_parse: MagicMock
    ) -> None:
        """Should use the config 'name' as the article source."""
        mock_parse.return_value = MagicMock(
            entries=[
                MagicMock(
                    **{
                        "get.side_effect": lambda key, default="": {
                            "title": "Article",
                            "link": "https://example.com/1",
                            "published": "2026-03-22",
                            "summary": "Summary",
                            "author": "",
                            "tags": [],
                        }.get(key, default),
                    }
                )
            ],
            feed=MagicMock(**{"get.return_value": "Feed Title"}),
        )

        config = [{"name": "El Tiempo", "url": "https://eltiempo.com/rss"}]
        results = collect_feeds_from_config(config, delay=0)

        assert len(results) == 1
        assert results[0]["source"] == "El Tiempo"
