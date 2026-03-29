"""Load all collected raw data (RSS, GDELT, ACLED) into DuckDB.

Reads JSON files from data/01_raw/, normalizes posts to the common schema,
and inserts them into the DuckDB database tables (posts, acled_events).

Usage:
    uv run python scripts/load_data_to_duckdb.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

# Add src to path so we can import project utilities
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from storage.db import create_tables, get_connection, insert_df
from utils.normalize import normalize_post

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(PROJECT_ROOT / "data" / "pulso_electoral.duckdb")

RAW_RSS_DIR = PROJECT_ROOT / "data" / "01_raw" / "rss"
RAW_GDELT_DIR = PROJECT_ROOT / "data" / "01_raw" / "gdelt"
RAW_ACLED_DIR = PROJECT_ROOT / "data" / "01_raw" / "acled"


def load_rss_articles(conn: object) -> int:
    """Load RSS articles from all JSON files in the raw directory.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Active DuckDB connection.

    Returns
    -------
    int
        Number of rows inserted.
    """
    json_files = sorted(RAW_RSS_DIR.glob("*.json"))
    if not json_files:
        print("  No RSS JSON files found.")
        return 0

    all_posts = []
    for fp in json_files:
        with open(fp) as f:
            articles = json.load(f)
        print(f"  Reading {fp.name}: {len(articles)} articles")
        for article in articles:
            normalized = normalize_post(article, "rss")
            # Map to posts table columns (drop raw_metadata, not in schema)
            all_posts.append(
                {
                    "id": normalized["id"],
                    "source": normalized["source"],
                    "platform": normalized["platform"],
                    "text": normalized["text"],
                    "author": normalized["author"],
                    "timestamp": normalized["timestamp"],
                    "url": normalized["url"],
                    "collected_at": normalized["collected_at"],
                }
            )

    if not all_posts:
        return 0

    df = pd.DataFrame(all_posts)
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], errors="coerce", utc=True, format="mixed"
    )
    df["collected_at"] = pd.to_datetime(df["collected_at"], errors="coerce")
    return insert_df(conn, "posts", df)


def load_gdelt_articles(conn: object) -> int:
    """Load GDELT articles from all JSON files in the raw directory.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Active DuckDB connection.

    Returns
    -------
    int
        Number of rows inserted.
    """
    json_files = sorted(RAW_GDELT_DIR.glob("*.json"))
    if not json_files:
        print("  No GDELT JSON files found.")
        return 0

    all_posts = []
    for fp in json_files:
        with open(fp) as f:
            articles = json.load(f)
        print(f"  Reading {fp.name}: {len(articles)} articles")
        for article in articles:
            # GDELT articles have different schema — normalize manually
            title = article.get("title", "")
            text = title  # GDELT DOC API articles only have title
            normalized = normalize_post(
                {
                    "text": text,
                    "title": title,
                    "source": article.get(
                        "source_domain", article.get("source", "gdelt")
                    ),
                    "author": article.get("source_domain", "unknown"),
                    "published": article.get("published", ""),
                    "url": article.get("url", ""),
                },
                "gdelt",
            )
            all_posts.append(
                {
                    "id": normalized["id"],
                    "source": normalized["source"],
                    "platform": normalized["platform"],
                    "text": normalized["text"],
                    "author": normalized["author"],
                    "timestamp": normalized["timestamp"],
                    "url": normalized["url"],
                    "collected_at": article.get(
                        "collected_at", datetime.now().isoformat()
                    ),
                }
            )

    if not all_posts:
        return 0

    df = pd.DataFrame(all_posts)
    # GDELT uses format like '20260314T024500Z' — try multiple formats
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], errors="coerce", utc=True, format="mixed"
    )
    df["collected_at"] = pd.to_datetime(df["collected_at"], errors="coerce")
    return insert_df(conn, "posts", df)


def _load_acled_filters() -> tuple[list[str], list[str]]:
    """Load allowed event types and combined notes keywords from config files.

    Combines keywords from three sources:
    - conf/data_collection/acled.yml  (notes_keywords + event_types)
    - conf/keywords/election.yml      (electoral process terms)
    - conf/keywords/civic_space.yml   (civic space / protest terms)

    This ensures the DB only retains events relevant to electoral monitoring and
    civic space health — filtering out Battles, Explosions, and generic armed
    conflict that make up the bulk of raw ACLED data for Colombia.

    Returns
    -------
    tuple[list[str], list[str]]
        (allowed_event_types, notes_keywords) — both lowercased for comparison.
    """
    with open(PROJECT_ROOT / "conf" / "data_collection" / "acled.yml") as f:
        acled_cfg = yaml.safe_load(f)
    with open(PROJECT_ROOT / "conf" / "keywords" / "election.yml") as f:
        election_cfg = yaml.safe_load(f)
    with open(PROJECT_ROOT / "conf" / "keywords" / "civic_space.yml") as f:
        civic_cfg = yaml.safe_load(f)

    # Allowed event types come exclusively from the ACLED config
    allowed_event_types = [et.lower() for et in acled_cfg["filters"]["event_types"]]

    # Combine notes_keywords from all three sources, deduplicated, lowercased
    raw_keywords: list[str] = (
        acled_cfg["settings"].get("notes_keywords", [])
        + election_cfg.get("keywords", [])
        + civic_cfg.get("keywords", [])
    )
    notes_keywords = list({kw.lower() for kw in raw_keywords})

    return allowed_event_types, notes_keywords


def load_acled_events(conn: object) -> int:
    """Load ACLED events from all JSON files in the raw directory.

    Applies event_type post-filtering to keep only research-relevant events:
    - event_type must be in the allowed list from acled.yml (excludes Battles,
      Explosions/Remote violence, etc.)

    NOTE: Spanish keyword filtering against ACLED notes is intentionally disabled.
    ACLED event notes are written in English, so Spanish keyword filters return
    near-zero results. The event_type filter (Protests, Riots, Violence against
    civilians, Strategic developments) already provides the correct research scope
    for electoral/civic space monitoring. The raw collection notebook also uses a
    fixed 90-day window anchored to known ACLED data availability.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Active DuckDB connection.

    Returns
    -------
    int
        Number of rows inserted (after filtering).
    """
    json_files = sorted(RAW_ACLED_DIR.glob("*.json"))
    if not json_files:
        print("  No ACLED JSON files found.")
        return 0

    allowed_event_types, _ = (
        _load_acled_filters()
    )  # notes_keywords unused (see docstring)

    all_events = []
    for fp in json_files:
        with open(fp) as f:
            events = json.load(f)
        print(f"  Reading {fp.name}: {len(events)} events")
        for event in events:
            all_events.append(
                {
                    "event_id": event.get("event_id_cnty", event.get("event_id", "")),
                    "event_date": event.get("event_date", ""),
                    "event_type": event.get("event_type", ""),
                    "sub_event_type": event.get("sub_event_type", ""),
                    "disorder_type": event.get("disorder_type", ""),
                    "actor1": event.get("actor1", ""),
                    "actor2": event.get("actor2", ""),
                    "assoc_actor_1": event.get("assoc_actor_1", ""),
                    "assoc_actor_2": event.get("assoc_actor_2", ""),
                    "inter1": str(event.get("inter1", "")),
                    "location": event.get("location", ""),
                    "latitude": float(event.get("latitude", 0)),
                    "longitude": float(event.get("longitude", 0)),
                    "geo_precision": int(event.get("geo_precision", 0)),
                    "admin1": event.get("admin1", ""),
                    "admin2": event.get("admin2", ""),
                    "civilian_targeting": event.get("civilian_targeting", ""),
                    "fatalities": int(event.get("fatalities", 0)),
                    "notes": event.get("notes", ""),
                    "source": event.get("source", ""),
                    "tags": event.get("tags", ""),
                }
            )

    if not all_events:
        return 0

    df = pd.DataFrame(all_events)
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce").dt.date

    raw_count = len(df)

    # Filter: Keep only allowed event types (drops Battles, Explosions, etc.)
    # The ACLED collection notebook already queries only these types, but this
    # provides a safety net for any stale raw files.
    df = df[df["event_type"].str.lower().isin(allowed_event_types)]

    print(
        f"  Loaded {raw_count} raw events, "
        f"{len(df)} match research scope (event_type filter)"
    )

    if df.empty:
        return 0

    return insert_df(conn, "acled_events", df)


def main() -> None:
    """Load all collected data into DuckDB."""
    print("=" * 60)
    print("Loading Collected Data into DuckDB")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Database: {DB_PATH}")
    print()

    conn = get_connection(DB_PATH)
    create_tables(conn)

    # Load RSS
    print("[1/3] Loading RSS articles...")
    rss_count = load_rss_articles(conn)
    print(f"  -> {rss_count} RSS posts loaded\n")

    # Load GDELT
    print("[2/3] Loading GDELT articles...")
    gdelt_count = load_gdelt_articles(conn)
    print(f"  -> {gdelt_count} GDELT posts loaded\n")

    # Load ACLED — clear stale unfiltered data before reload
    print("[3/3] Loading ACLED events...")
    print("  Clearing stale ACLED data before reload...")
    conn.execute("DELETE FROM acled_events")
    acled_count = load_acled_events(conn)
    print(f"  -> {acled_count} ACLED events loaded\n")

    # Verify
    print("=" * 60)
    print("Verification:")
    print("=" * 60)

    post_count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()
    acled_total = conn.execute("SELECT COUNT(*) FROM acled_events").fetchone()
    platforms = conn.execute("SELECT DISTINCT platform FROM posts").fetchdf()

    print(f"  Total posts: {post_count[0] if post_count else 0}")
    print(f"  Total ACLED events: {acled_total[0] if acled_total else 0}")
    print(
        f"  Platforms: {', '.join(platforms['platform'].tolist()) if not platforms.empty else 'none'}"
    )

    # Post counts by platform
    by_platform = conn.execute(
        "SELECT platform, COUNT(*) as cnt FROM posts GROUP BY platform ORDER BY cnt DESC"
    ).fetchdf()
    if not by_platform.empty:
        print("\n  Posts by platform:")
        for _, row in by_platform.iterrows():
            print(f"    {row['platform']}: {row['cnt']}")

    # ACLED event type distribution
    by_type = conn.execute(
        "SELECT event_type, COUNT(*) as cnt FROM acled_events GROUP BY event_type ORDER BY cnt DESC"
    ).fetchdf()
    if not by_type.empty:
        print("\n  ACLED events by type:")
        for _, row in by_type.iterrows():
            print(f"    {row['event_type']}: {row['cnt']}")

    conn.close()
    print(f"\n{'=' * 60}")
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
