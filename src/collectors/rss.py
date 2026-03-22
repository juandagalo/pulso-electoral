"""RSS feed collection utilities."""

from __future__ import annotations

import time

import feedparser


def collect_feeds(feed_urls: list[str], delay: float = 1.0) -> list[dict]:
    """Collect articles from a list of RSS feed URLs.

    Parameters
    ----------
    feed_urls : list[str]
        URLs of RSS feeds to collect from.
    delay : float
        Seconds to wait between feed requests. Defaults to 1.0.

    Returns
    -------
    list[dict]
        List of article dicts with keys: title, link, published, summary, source.
    """
    articles = []
    for url in feed_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "source": feed.feed.get("title", url),
                "url": entry.get("link", ""),
                "author": entry.get("author", ""),
                "categories": [tag.get("term", "") for tag in entry.get("tags", [])],
            })
        time.sleep(delay)
    return articles


def collect_feeds_from_config(feeds_config: list[dict], delay: float = 1.0) -> list[dict]:
    """Collect articles using a list of feed config dictionaries.

    Parameters
    ----------
    feeds_config : list[dict]
        List of dicts with 'name' and 'url' keys (from rss_feeds.yml).
    delay : float
        Seconds to wait between feed requests. Defaults to 1.0.

    Returns
    -------
    list[dict]
        List of article dicts with source metadata from config.
    """
    articles = []
    for feed_info in feeds_config:
        url = feed_info["url"]
        name = feed_info.get("name", url)
        feed = feedparser.parse(url)
        for entry in feed.entries:
            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "source": name,
                "url": entry.get("link", ""),
                "author": entry.get("author", ""),
                "categories": [tag.get("term", "") for tag in entry.get("tags", [])],
            })
        time.sleep(delay)
    return articles
