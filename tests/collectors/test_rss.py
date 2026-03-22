"""Tests for RSS feed collection utilities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests

from collectors.rss import collect_feeds, collect_feeds_from_config

# Minimal valid RSS 2.0 XML with one item, used as the default mock response body.
SAMPLE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <link>https://example.com</link>
    <item>
      <title>Test Article</title>
      <link>https://example.com/article</link>
      <pubDate>Sat, 22 Mar 2026 00:00:00 GMT</pubDate>
      <description>Test summary</description>
      <author>Test Author</author>
    </item>
  </channel>
</rss>
"""

SAMPLE_XML_TWO_ITEMS = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Second Feed</title>
    <link>https://example2.com</link>
    <item>
      <title>Article A</title>
      <link>https://example2.com/a</link>
      <pubDate>Sat, 22 Mar 2026 01:00:00 GMT</pubDate>
      <description>Summary A</description>
    </item>
    <item>
      <title>Article B</title>
      <link>https://example2.com/b</link>
      <pubDate>Sat, 22 Mar 2026 02:00:00 GMT</pubDate>
      <description>Summary B</description>
    </item>
  </channel>
</rss>
"""

EMPTY_FEED_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Empty Feed</title>
    <link>https://example.com/empty</link>
  </channel>
</rss>
"""


_HTTP_ERROR_THRESHOLD = 400


def _make_response(text: str = SAMPLE_XML, status_code: int = 200) -> MagicMock:
    """Create a mock requests.Response returning *text* with raise_for_status."""
    resp = MagicMock(spec=requests.Response)
    resp.text = text
    resp.status_code = status_code
    if status_code >= _HTTP_ERROR_THRESHOLD:
        resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    else:
        resp.raise_for_status.return_value = None
    return resp


class TestCollectFeeds:
    """Tests for the collect_feeds function."""

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_returns_articles(
        self, mock_get: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Collect feeds should return a list of article dicts parsed from RSS XML."""
        mock_get.return_value = _make_response(SAMPLE_XML)

        results = collect_feeds(["https://example.com/rss"], delay=0)

        assert len(results) == 1
        assert results[0]["title"] == "Test Article"
        assert results[0]["source"] == "Test Feed"
        # feedparser receives response text, NOT a URL
        mock_get.assert_called_once_with("https://example.com/rss", timeout=30)

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_empty_feed(self, mock_get: MagicMock, mock_sleep: MagicMock) -> None:
        """Collect feeds should handle empty feeds gracefully."""
        mock_get.return_value = _make_response(EMPTY_FEED_XML)

        results = collect_feeds(["https://example.com/empty"], delay=0)

        assert results == []

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_multiple_urls(self, mock_get: MagicMock, mock_sleep: MagicMock) -> None:
        """Collect feeds should process multiple URLs."""
        mock_get.return_value = _make_response(SAMPLE_XML)

        collect_feeds(["https://a.com/rss", "https://b.com/rss"], delay=0)

        assert mock_get.call_count == 2  # noqa: PLR2004

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_default_timeout(
        self, mock_get: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Default timeout of 30s should be forwarded to requests.get."""
        mock_get.return_value = _make_response(SAMPLE_XML)

        collect_feeds(["https://example.com/rss"], delay=0)

        mock_get.assert_called_once_with("https://example.com/rss", timeout=30)

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_custom_timeout(self, mock_get: MagicMock, mock_sleep: MagicMock) -> None:
        """Explicit timeout=10 should be forwarded to requests.get."""
        mock_get.return_value = _make_response(SAMPLE_XML)

        collect_feeds(["https://example.com/rss"], delay=0, timeout=10)

        mock_get.assert_called_once_with("https://example.com/rss", timeout=10)

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_timeout_exception(
        self, mock_get: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """First URL raises Timeout; second feed articles are still returned."""
        mock_get.side_effect = [
            requests.Timeout("timed out"),
            _make_response(SAMPLE_XML),
        ]

        results = collect_feeds(["https://slow.com/rss", "https://fast.com/rss"], delay=0)

        assert len(results) == 1
        assert results[0]["title"] == "Test Article"

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_http_error(self, mock_get: MagicMock, mock_sleep: MagicMock) -> None:
        """raise_for_status raises HTTPError; empty list returned, no exception."""
        mock_get.return_value = _make_response(SAMPLE_XML, status_code=500)

        results = collect_feeds(["https://broken.com/rss"], delay=0)

        assert results == []

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_connection_error(
        self, mock_get: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """ConnectionError on first URL; remaining feeds still processed."""
        mock_get.side_effect = [
            requests.ConnectionError("connection refused"),
            _make_response(SAMPLE_XML_TWO_ITEMS),
        ]

        results = collect_feeds(["https://down.com/rss", "https://up.com/rss"], delay=0)

        assert len(results) == 2  # noqa: PLR2004
        assert results[0]["title"] == "Article A"
        assert results[1]["title"] == "Article B"

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_all_fail(self, mock_get: MagicMock, mock_sleep: MagicMock) -> None:
        """When all feeds error, empty list is returned with no exception raised."""
        mock_get.side_effect = requests.ConnectionError("all down")

        results = collect_feeds(["https://a.com/rss", "https://b.com/rss"], delay=0)

        assert results == []


class TestCollectFeedsFromConfig:
    """Tests for the collect_feeds_from_config function."""

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_uses_config_name_as_source(self, mock_get: MagicMock, mock_sleep: MagicMock) -> None:
        """Should use the config 'name' as the article source."""
        mock_get.return_value = _make_response(SAMPLE_XML)

        config = [{"name": "El Tiempo", "url": "https://eltiempo.com/rss"}]
        results = collect_feeds_from_config(config, delay=0)

        assert len(results) == 1
        assert results[0]["source"] == "El Tiempo"

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_from_config_reads_timeout_from_settings(
        self, mock_get: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """settings.timeout_seconds should override the default timeout."""
        mock_get.return_value = _make_response(SAMPLE_XML)

        config = [{"name": "Feed", "url": "https://example.com/rss"}]
        settings = {"timeout_seconds": 15}
        collect_feeds_from_config(config, delay=0, settings=settings)

        mock_get.assert_called_once_with("https://example.com/rss", timeout=15)

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_from_config_enabled_false_skipped(
        self, mock_get: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Feeds with enabled: false should not be fetched."""
        mock_get.return_value = _make_response(SAMPLE_XML)

        config = [
            {"name": "Active", "url": "https://active.com/rss"},
            {"name": "Disabled", "url": "https://disabled.com/rss", "enabled": False},
        ]
        results = collect_feeds_from_config(config, delay=0)

        # Only the active feed should be fetched
        assert mock_get.call_count == 1
        mock_get.assert_called_once_with("https://active.com/rss", timeout=30)
        assert len(results) == 1

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_from_config_partial_failure(
        self, mock_get: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """One config feed fails, others succeed -- partial results returned."""
        mock_get.side_effect = [
            _make_response(SAMPLE_XML),
            requests.ConnectionError("down"),
            _make_response(SAMPLE_XML_TWO_ITEMS),
        ]

        config = [
            {"name": "Feed1", "url": "https://one.com/rss"},
            {"name": "Feed2", "url": "https://two.com/rss"},
            {"name": "Feed3", "url": "https://three.com/rss"},
        ]
        results = collect_feeds_from_config(config, delay=0)

        # Feed1 (1 article) + Feed3 (2 articles) = 3 total
        assert len(results) == 3  # noqa: PLR2004

    @patch("collectors.rss.time.sleep")
    @patch("collectors.rss.requests.get")
    def test_collect_feeds_from_config_default_timeout(
        self, mock_get: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Without settings, default timeout=30 should be used."""
        mock_get.return_value = _make_response(SAMPLE_XML)

        config = [{"name": "Feed", "url": "https://example.com/rss"}]
        collect_feeds_from_config(config, delay=0)

        mock_get.assert_called_once_with("https://example.com/rss", timeout=30)
