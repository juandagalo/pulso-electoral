"""Simple DuckDB database helpers."""

from __future__ import annotations

import duckdb
import pandas as pd


def get_connection(db_path: str = "data/pulso_electoral.db") -> duckdb.DuckDBPyConnection:
    """Get or create a DuckDB connection.

    Parameters
    ----------
    db_path : str
        Path to the DuckDB database file. Defaults to 'data/pulso_electoral.db'.

    Returns
    -------
    duckdb.DuckDBPyConnection
        DuckDB connection object.
    """
    return duckdb.connect(db_path)


def create_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all tables if they don't exist.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Active DuckDB connection.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id VARCHAR PRIMARY KEY,
            source VARCHAR,
            platform VARCHAR,
            text TEXT,
            author VARCHAR,
            timestamp TIMESTAMP,
            url VARCHAR,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS nlp_results (
            post_id VARCHAR,
            task VARCHAR,
            label VARCHAR,
            score FLOAT,
            details JSON,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (post_id, task)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY,
            timestamp TIMESTAMP,
            metric VARCHAR,
            value FLOAT,
            z_score FLOAT,
            rolling_mean FLOAT,
            rolling_std FLOAT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS acled_events (
            event_id VARCHAR PRIMARY KEY,
            event_date DATE,
            event_type VARCHAR,
            sub_event_type VARCHAR,
            disorder_type VARCHAR,
            actor1 VARCHAR,
            actor2 VARCHAR,
            assoc_actor_1 VARCHAR,
            assoc_actor_2 VARCHAR,
            inter1 INTEGER,
            location VARCHAR,
            latitude FLOAT,
            longitude FLOAT,
            geo_precision INTEGER,
            admin1 VARCHAR,
            admin2 VARCHAR,
            civilian_targeting VARCHAR,
            fatalities INTEGER,
            notes TEXT,
            source VARCHAR,
            tags TEXT
        )
    """)

    _migrate_acled_events(conn)


_ACLED_MIGRATION_COLUMNS: list[tuple[str, str]] = [
    ("disorder_type", "VARCHAR"),
    ("assoc_actor_1", "VARCHAR"),
    ("assoc_actor_2", "VARCHAR"),
    ("inter1", "INTEGER"),
    ("geo_precision", "INTEGER"),
    ("civilian_targeting", "VARCHAR"),
    ("tags", "TEXT"),
]


def _migrate_acled_events(conn: duckdb.DuckDBPyConnection) -> None:
    """Add new columns to an existing acled_events table idempotently.

    Uses ALTER TABLE ADD COLUMN IF NOT EXISTS so it is safe to run on
    databases that already have the latest schema.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Active DuckDB connection.
    """
    for col_name, col_type in _ACLED_MIGRATION_COLUMNS:
        conn.execute(
            f"ALTER TABLE acled_events ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
        )


def insert_df(conn: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame) -> int:
    """Insert a DataFrame into a table. Returns rows inserted.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Active DuckDB connection.
    table : str
        Target table name.
    df : pd.DataFrame
        DataFrame to insert.

    Returns
    -------
    int
        Number of rows inserted.
    """
    if df.empty:
        return 0
    conn.execute(f"INSERT OR IGNORE INTO {table} SELECT * FROM df")  # noqa: S608
    return len(df)


def query(conn: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    """Run a SQL query and return a DataFrame.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Active DuckDB connection.
    sql : str
        SQL query string.

    Returns
    -------
    pd.DataFrame
        Query results as a DataFrame.
    """
    return conn.execute(sql).fetchdf()
