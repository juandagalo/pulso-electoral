"""RSS feed collection utilities."""

from __future__ import annotations

import logging
import time

import feedparser
import requests
import urllib3

# Some hosts advertise AAAA records but do not respond on IPv6, causing Python's
# socket layer to stall until the OS-level connect timeout fires (often 130 s).
# Forcing IPv4-only here makes requests.get() respect our timeout parameter.
urllib3.util.connection.HAS_IPV6 = False  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)

_FIELDS = ("title", "link", "published", "summary", "author")


def collect_feeds(
    feed_urls: list[str], delay: float = 1.0, timeout: int = 30
) -> list[dict]:
    """Fetch each URL with *timeout* seconds, parse RSS, return article dicts."""
    articles: list[dict] = []
    for url in feed_urls:
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            source = feed.feed.get("title", url)
            for e in feed.entries:
                row = {f: e.get(f, "") for f in _FIELDS}
                row.update(source=source, url=e.get("link", ""))
                row["categories"] = [t.get("term", "") for t in e.get("tags", [])]
                articles.append(row)
        except requests.RequestException as exc:
            logger.warning("Failed to fetch feed %s: %s", url, exc)
            continue
        time.sleep(delay)
    return articles


def collect_feeds_from_config(
    feeds_config: list[dict],
    delay: float = 1.0,
    timeout: int = 30,
    settings: dict | None = None,
) -> list[dict]:
    """Collect from config dicts; *settings.timeout_seconds* overrides *timeout*."""
    if settings and "timeout_seconds" in settings:
        timeout = int(settings["timeout_seconds"])
    articles: list[dict] = []
    for feed_info in feeds_config:
        if not feed_info.get("enabled", True):
            logger.info("Skipping disabled feed: %s", feed_info.get("name", "unknown"))
            continue
        url, name = feed_info["url"], feed_info.get("name", feed_info["url"])
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            for e in feed.entries:
                row = {f: e.get(f, "") for f in _FIELDS}
                row.update(source=name, url=e.get("link", ""))
                row["categories"] = [t.get("term", "") for t in e.get("tags", [])]
                articles.append(row)
        except requests.RequestException as exc:
            logger.warning("Failed to fetch feed %s: %s", url, exc)
            continue
        time.sleep(delay)
    return articles
