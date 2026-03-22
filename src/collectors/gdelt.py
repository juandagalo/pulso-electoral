"""GDELT data collection utilities."""

from __future__ import annotations

import time

import pandas as pd
import requests


def query_gdelt(
    country: str = "Colombia",
    keywords: list[str] | None = None,
    date_range: tuple[str, str] | None = None,
    max_records: int = 250,
) -> pd.DataFrame:
    """Query GDELT DOC API for articles matching filters.

    Parameters
    ----------
    country : str
        Country name to filter by. Defaults to 'Colombia'.
    keywords : list[str] | None
        Keywords to search for in article content.
    date_range : tuple[str, str] | None
        Start and end dates as (YYYYMMDDHHMMSS, YYYYMMDDHHMMSS).
    max_records : int
        Maximum number of records to return. Defaults to 250.

    Returns
    -------
    pd.DataFrame
        DataFrame with GDELT article data.
    """
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"

    query_parts = [f'sourcecountry:"{country}"']
    if keywords:
        keyword_query = " OR ".join(f'"{kw}"' for kw in keywords[:10])
        query_parts.append(f"({keyword_query})")

    params: dict[str, str | int] = {
        "query": " ".join(query_parts),
        "mode": "ArtList",
        "maxrecords": max_records,
        "format": "json",
        "sort": "DateDesc",
    }

    if date_range:
        params["startdatetime"] = date_range[0]
        params["enddatetime"] = date_range[1]

    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    articles = data.get("articles", [])

    if not articles:
        return pd.DataFrame()

    records = []
    for article in articles:
        records.append(
            {
                "url": article.get("url", ""),
                "title": article.get("title", ""),
                "source_domain": article.get("domain", ""),
                "published": article.get("seendate", ""),
                "tone": article.get("tone", 0.0),
                "language": article.get("language", ""),
                "source": "gdelt",
            }
        )

    time.sleep(2.0)  # Respect soft rate limits
    return pd.DataFrame(records)
