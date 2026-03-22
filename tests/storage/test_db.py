"""Tests for DuckDB storage utilities."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from storage.db import _migrate_acled_events, create_tables, get_connection, insert_df, query

_ACLED_COLUMN_COUNT = 21
# Original 14-column schema before the hardening migration added 7 new columns.
# The 7 columns added by _migrate_acled_events are:
#   disorder_type, assoc_actor_1, assoc_actor_2, inter1, geo_precision,
#   civilian_targeting, tags
_OLD_ACLED_COLUMNS = [
    "event_id VARCHAR PRIMARY KEY",
    "event_date DATE",
    "event_type VARCHAR",
    "sub_event_type VARCHAR",
    "actor1 VARCHAR",
    "actor2 VARCHAR",
    "location VARCHAR",
    "latitude FLOAT",
    "longitude FLOAT",
    "admin1 VARCHAR",
    "admin2 VARCHAR",
    "fatalities INTEGER",
    "notes TEXT",
    "source VARCHAR",
]


class TestDuckDBHelpers:
    """Tests for DuckDB helper functions."""

    def test_get_connection(self, tmp_path: Path) -> None:
        """Should create a DuckDB connection."""
        db_path = str(tmp_path / "test.db")
        conn = get_connection(db_path)
        assert conn is not None
        conn.close()

    def test_create_tables(self, tmp_path: Path) -> None:
        """Should create all required tables."""
        db_path = str(tmp_path / "test.db")
        conn = get_connection(db_path)
        create_tables(conn)

        # Check that tables exist
        tables = conn.execute("SHOW TABLES").fetchdf()
        table_names = tables["name"].tolist()

        assert "posts" in table_names
        assert "nlp_results" in table_names
        assert "anomalies" in table_names
        assert "acled_events" in table_names

        conn.close()

    def test_insert_and_query(self, tmp_path: Path) -> None:
        """Should insert a DataFrame and query it back."""
        db_path = str(tmp_path / "test.db")
        conn = get_connection(db_path)
        create_tables(conn)

        df = pd.DataFrame(
            [
                {
                    "id": "test001",
                    "source": "rss",
                    "platform": "rss",
                    "text": "Test post about Colombian elections",
                    "author": "test_author",
                    "timestamp": "2026-03-22 10:00:00",
                    "url": "https://example.com/1",
                    "collected_at": "2026-03-22 10:05:00",
                }
            ]
        )

        rows = insert_df(conn, "posts", df)
        assert rows == 1

        result = query(conn, "SELECT * FROM posts")
        assert len(result) == 1
        assert result.iloc[0]["id"] == "test001"

        conn.close()

    def test_insert_empty_df(self, tmp_path: Path) -> None:
        """Should handle empty DataFrame gracefully."""
        db_path = str(tmp_path / "test.db")
        conn = get_connection(db_path)
        create_tables(conn)

        df = pd.DataFrame()
        rows = insert_df(conn, "posts", df)
        assert rows == 0

        conn.close()

    def test_query_empty_table(self, tmp_path: Path) -> None:
        """Should return empty DataFrame for empty table."""
        db_path = str(tmp_path / "test.db")
        conn = get_connection(db_path)
        create_tables(conn)

        result = query(conn, "SELECT * FROM posts")
        assert len(result) == 0

        conn.close()


class TestMigrateAcledEvents:
    """Tests for the _migrate_acled_events migration helper."""

    def _create_old_schema(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Create the 14-column pre-migration acled_events table."""
        col_defs = ", ".join(_OLD_ACLED_COLUMNS)
        conn.execute(f"CREATE TABLE acled_events ({col_defs})")

    def test_migrate_adds_missing_columns(self) -> None:
        """Should add the 7 new columns to an old 14-column acled_events table."""
        conn = duckdb.connect(":memory:")
        self._create_old_schema(conn)

        _migrate_acled_events(conn)

        columns_df = conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'acled_events' ORDER BY ordinal_position"
        ).fetchdf()
        assert len(columns_df) == _ACLED_COLUMN_COUNT

    def test_migrate_idempotent(self) -> None:
        """Running _migrate_acled_events twice should not raise and should keep exactly 21 columns."""
        conn = duckdb.connect(":memory:")
        self._create_old_schema(conn)

        _migrate_acled_events(conn)
        _migrate_acled_events(conn)  # second run — idempotency check

        columns_df = conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'acled_events' ORDER BY ordinal_position"
        ).fetchdf()
        assert len(columns_df) == _ACLED_COLUMN_COUNT
