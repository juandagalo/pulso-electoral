"""Shared test fixtures for Pulso Electoral tests."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest


@pytest.fixture
def sample_posts() -> list[dict]:
    """Sample Colombian political posts for testing."""
    return [
        {
            "id": "test001",
            "text": "Petro anuncia nueva reforma tributaria para el 2026",
            "source": "El Tiempo",
            "platform": "rss",
            "author": "Redaccion Politica",
            "timestamp": "2026-03-20T10:00:00",
            "url": "https://eltiempo.com/politica/reforma-tributaria",
        },
        {
            "id": "test002",
            "text": "Las bodegas digitales estan en plena actividad para las elecciones",
            "source": "GDELT",
            "platform": "gdelt",
            "author": "GDELT",
            "timestamp": "2026-03-20T14:30:00",
            "url": "https://gdeltproject.org/abc123",
        },
        {
            "id": "test003",
            "text": "Fico Gutierrez lidera las encuestas presidenciales segun Invamer",
            "source": "El Espectador",
            "platform": "rss",
            "author": "Andres Martinez",
            "timestamp": "2026-03-21T08:00:00",
            "url": "https://elespectador.com/politica/encuestas-fico",
        },
        {
            "id": "test004",
            "text": "Gonorrea, otra vez subio la gasolina. Este gobierno mamerto nos tiene jodidos",
            "source": "Pulzo",
            "platform": "rss",
            "author": "Redaccion",
            "timestamp": "2026-03-21T16:00:00",
            "url": "https://pulzo.com/nacion/gasolina-sube",
        },
        {
            "id": "test005",
            "text": "Asesinan a lider social en el Cauca. Van 45 lideres asesinados en 2026.",
            "source": "acled",
            "platform": "acled",
            "author": "ACLED",
            "timestamp": "2026-03-21T20:00:00",
            "url": "https://acleddata.com/colombia",
        },
    ]


@pytest.fixture
def sample_texts() -> list[str]:
    """Sample Spanish texts for NLP testing."""
    return [
        "Petro anuncia nueva reforma tributaria para el 2026",
        "Las bodegas digitales estan en plena actividad para las elecciones",
        "Fico Gutierrez lidera las encuestas presidenciales",
        "Asesinan a lider social en el Cauca",
        "La paz total es una chimba de idea, parcero",
    ]


@pytest.fixture
def temp_db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    """Create a temporary DuckDB database for testing."""
    from storage.db import create_tables, get_connection

    db_path = str(tmp_path / "test.db")
    conn = get_connection(db_path)
    create_tables(conn)
    return conn


@pytest.fixture
def sample_config(tmp_path: Path) -> Path:
    """Create a temporary YAML config file for testing."""
    config = {
        "feeds": [
            {"name": "Test Feed", "url": "https://example.com/rss"},
            {"name": "Test Feed 2", "url": "https://example.com/rss2"},
        ],
        "settings": {"request_delay_seconds": 0.1},
    }
    config_path = tmp_path / "test_config.yml"
    import yaml

    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def sample_posts_json(tmp_path: Path) -> Path:
    """Create a temporary sample posts JSON file."""
    posts = [
        {
            "id": "s001",
            "text": "Elecciones presidenciales Colombia 2026",
            "source": "test",
            "platform": "test",
            "author": "test_user",
            "timestamp": "2026-03-22T00:00:00",
            "url": "https://example.com/1",
        }
    ]
    path = tmp_path / "sample.json"
    with open(path, "w") as f:
        json.dump(posts, f)
    return path
