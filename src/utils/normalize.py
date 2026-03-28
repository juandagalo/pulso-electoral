"""Post normalization to common schema across all data sources."""

from __future__ import annotations

import hashlib
from datetime import datetime


def normalize_post(raw_post: dict, source: str) -> dict:
    """Normalize a raw post from any source to the common schema.

    Parameters
    ----------
    raw_post : dict
        Raw post data from a collector.
    source : str
        Source platform name (e.g., 'rss', 'gdelt', 'acled').

    Returns
    -------
    dict
        Normalized post with keys: id, text, source, platform, author, timestamp, url,
        collected_at, raw_metadata.
    """
    text = _extract_text(raw_post, source)
    post_id = _generate_id(text, source, raw_post.get("url", ""))

    return {
        "id": post_id,
        "text": text,
        "source": raw_post.get("source", source),
        "platform": source,
        "author": raw_post.get("author", "unknown"),
        "timestamp": raw_post.get("published", raw_post.get("timestamp", "")),
        "url": raw_post.get("url", raw_post.get("link", "")),
        "collected_at": datetime.now().isoformat(),
        "raw_metadata": {
            k: v for k, v in raw_post.items() if k not in ("text", "content")
        },
    }


def _extract_text(raw_post: dict, source: str) -> str:
    """Extract the primary text field from a raw post.

    Parameters
    ----------
    raw_post : dict
        Raw post data.
    source : str
        Source platform name.

    Returns
    -------
    str
        Extracted text content.
    """
    if source == "rss":
        title = raw_post.get("title", "")
        summary = raw_post.get("summary", "")
        return f"{title}. {summary}" if summary else title
    return str(raw_post.get("text", raw_post.get("content", "")))


def _generate_id(text: str, source: str, url: str) -> str:
    """Generate a deterministic ID from post content.

    Parameters
    ----------
    text : str
        Post text content.
    source : str
        Source platform name.
    url : str
        Post URL.

    Returns
    -------
    str
        SHA-256 based ID string.
    """
    content = f"{source}:{url}:{text[:200]}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]
