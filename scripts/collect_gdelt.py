"""One-off GDELT DOC API collection script for Colombia election/civic data.

Queries GDELT DOC API (free, no auth) for Colombian articles across
election, civic space, and manipulation keyword categories.
Saves results to data/01_raw/gdelt/gdelt_articles_YYYYMMDD.json.

Usage:
    uv run python scripts/collect_gdelt.py
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import requests

# --- Configuration ---

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
REQUEST_TIMEOUT = 120
RATE_LIMIT_DELAY = 3.0  # seconds between requests
MAX_RECORDS = 250
TIMESPAN = "30d"

# Keyword groups — GDELT DOC API requires OR'd terms wrapped in ()
# Each query uses "Colombia" as anchor + parenthesized OR group
QUERY_GROUPS: dict[str, str] = {
    "election_es": 'Colombia (elecciones OR candidato OR votacion OR "campana electoral" OR presidente)',
    "election_en": 'Colombia (election OR candidate OR voting OR "presidential race" OR 2026)',
    "civic_space": 'Colombia ("protesta social" OR "lideres sociales" OR "derechos humanos" OR "libertad de prensa")',
    "manipulation": 'Colombia (desinformacion OR "noticias falsas" OR "manipulacion" OR "fake news" OR bots)',
    "protests": "Colombia (protests OR manifestaciones OR ESMAD OR paro OR marcha)",
    "conflict": 'Colombia (conflict OR "violencia politica" OR guerrilla OR FARC OR "paz total")',
    "democracy": 'Colombia (democracia OR "sociedad civil" OR "espacio civico" OR congreso)',
    "press_freedom": 'Colombia ("libertad de expresion" OR censura OR periodistas OR "press freedom")',
}

OUTPUT_DIR = Path("data/01_raw/gdelt")


def fetch_gdelt_articles(query: str, label: str) -> list[dict[str, object]]:
    """Fetch articles from GDELT DOC API for a single query."""
    params = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": MAX_RECORDS,
        "format": "json",
        "sort": "DateDesc",
        "timespan": TIMESPAN,
    }

    print(f"\n  [{label}] Query: {query[:80]}...")
    print(f"  [{label}] URL params: timespan={TIMESPAN}, maxrecords={MAX_RECORDS}")

    try:
        response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # Check if response is actually JSON (GDELT returns text/html for errors)
        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type:
            print(
                f"  [{label}] Non-JSON response ({content_type}): {response.text[:200]}"
            )
            return []

        data = response.json()
        articles = data.get("articles", [])

        print(f"  [{label}] Got {len(articles)} articles")
        return list(articles)

    except requests.exceptions.Timeout:
        print(f"  [{label}] TIMEOUT after {REQUEST_TIMEOUT}s - skipping")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"  [{label}] HTTP error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"  [{label}] Request failed: {e}")
        return []
    except json.JSONDecodeError:
        print(f"  [{label}] Failed to parse JSON response: {response.text[:200]}")
        return []


def deduplicate_articles(articles: list[dict[str, object]]) -> list[dict[str, object]]:
    """Deduplicate articles by URL."""
    seen_urls: set[str] = set()
    unique: list[dict[str, object]] = []

    for article in articles:
        url = str(article.get("url", ""))
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(article)

    return unique


def normalize_article(article: dict[str, object]) -> dict[str, object]:
    """Normalize a GDELT article to our common schema."""
    return {
        "url": article.get("url", ""),
        "title": article.get("title", ""),
        "source_domain": article.get("domain", ""),
        "published": article.get("seendate", ""),
        "tone": article.get("tone", 0.0),
        "language": article.get("language", ""),
        "source_country": article.get("sourcecountry", ""),
        "socialimage": article.get("socialimage", ""),
        "source": "gdelt",
        "collected_at": datetime.now().isoformat(),
    }


def main() -> None:
    """Run GDELT collection across all keyword groups."""
    print("=" * 60)
    print("GDELT DOC API Collection - Pulso Electoral Colombia 2026")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Timespan: {TIMESPAN}")
    print(f"Max records per query: {MAX_RECORDS}")
    print(f"Query groups: {len(QUERY_GROUPS)}")

    all_raw_articles: list[dict[str, object]] = []

    for label, query in QUERY_GROUPS.items():
        articles = fetch_gdelt_articles(query, label)
        all_raw_articles.extend(articles)

        # Respect rate limits
        if label != list(QUERY_GROUPS.keys())[-1]:
            print(f"  Waiting {RATE_LIMIT_DELAY}s (rate limit)...")
            time.sleep(RATE_LIMIT_DELAY)

    print(f"\n{'=' * 60}")
    print(f"Total raw articles (before dedup): {len(all_raw_articles)}")

    # Deduplicate
    unique_articles = deduplicate_articles(all_raw_articles)
    print(f"Unique articles (after dedup): {len(unique_articles)}")

    if not unique_articles:
        print("\nNo articles collected. Check network/API availability.")
        return

    # Normalize to our schema
    normalized = [normalize_article(a) for a in unique_articles]

    # Summary stats
    domains: dict[str, int] = {}
    languages: dict[str, int] = {}
    for article in normalized:
        domain = str(article.get("source_domain", "unknown"))
        lang = str(article.get("language", "unknown"))
        domains[domain] = domains.get(domain, 0) + 1
        languages[lang] = languages.get(lang, 0) + 1

    print(f"\nLanguage distribution:")
    for lang, count in sorted(languages.items(), key=lambda x: -x[1])[:10]:
        print(f"  {lang}: {count}")

    print(f"\nTop 15 source domains:")
    for domain, count in sorted(domains.items(), key=lambda x: -x[1])[:15]:
        print(f"  {domain}: {count}")

    # Tone stats
    tones = [float(a.get("tone", 0)) for a in normalized if a.get("tone")]
    if tones:
        avg_tone = sum(tones) / len(tones)
        min_tone = min(tones)
        max_tone = max(tones)
        negative = sum(1 for t in tones if t < 0)
        positive = sum(1 for t in tones if t > 0)
        print(f"\nTone statistics:")
        print(f"  Average: {avg_tone:.2f}")
        print(f"  Range: [{min_tone:.2f}, {max_tone:.2f}]")
        print(f"  Negative articles: {negative}")
        print(f"  Positive articles: {positive}")
        print(f"  Neutral (0): {len(tones) - negative - positive}")

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    output_path = OUTPUT_DIR / f"gdelt_articles_{today}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"SAVED: {len(normalized)} articles to {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")
    print("=" * 60)


if __name__ == "__main__":
    main()
