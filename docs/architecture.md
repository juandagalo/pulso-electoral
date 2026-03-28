# Architecture Overview

Pulso Electoral Colombia 2026 follows a research-first architecture where notebooks are the primary deliverable and source utilities provide thin reusable helpers.

## Design Philosophy

1. **Notebooks tell the story** -- collection, analysis, and findings are presented as reproducible narratives
2. **src/ is support, not the product** -- simple utility functions called from notebooks
3. **HuggingFace models used directly** -- `pysentimiento` and `spaCy` invoked in notebooks, not wrapped
4. **YAML configs, not Pydantic** -- `yaml.safe_load()` for simplicity and non-engineer editability
5. **DuckDB for storage** -- zero-infrastructure analytical database in a single file

## Data Flow

```
Colombian RSS Feeds ----\
GDELT Project -----------+--> data/01_raw/
ACLED Data --------------/        |
                                  v
                           data/02_intermediate/ (common schema)
                                  |
                                  v
                           data/03_primary/ (cleaned, deduplicated)
                                  |
                                  v
                           data/04_enriched/ (sentiment, NER, topics)
                                  |
                                  v
                           data/05_analysis/ (aggregated results)
                                  |
                                  v
                           data/06_reporting/ (data packages for CIVICUS)
```

## NLP Pipeline

| Task | Tool | Model |
|------|------|-------|
| Sentiment Analysis | pysentimiento | robertuito-sentiment-analysis |
| Emotion Detection | pysentimiento | robertuito-emotion-analysis |
| Hate Speech Detection | pysentimiento | robertuito-hate-speech |
| Named Entity Recognition | spaCy | es_core_news_lg |
| Topic Modeling | sentence-transformers + sklearn | paraphrase-multilingual-MiniLM-L12-v2 |
| Language Detection | langdetect | -- |

## Configuration

Split YAML files in `conf/` organized by domain:

- `conf/config.yml` -- global project settings
- `conf/data_collection/` -- source-specific collection parameters
- `conf/keywords/` -- keyword lists by research category
- `conf/nlp/` -- model names and task configurations

## Storage Strategy & Scalability Path

### Why DuckDB (Demo Phase)

| Requirement | How DuckDB Meets It |
|-------------|-------------------|
| Zero infrastructure | Embedded database — single file, no server, no Docker service needed |
| Analytical queries | Column-oriented engine optimized for aggregations, GROUP BY, window functions |
| Pandas integration | Native DataFrame ingestion — `INSERT INTO table SELECT * FROM df` |
| Parquet compatibility | Reads/writes Parquet files directly — data layers remain portable |
| SQL interface | Research team can query data with standard SQL — lower barrier for capacity building |
| Reproducibility | Database file travels with the project — anyone can reproduce the analysis |
| Cost | Free, open-source, MIT licensed |

### Data Volume Expectations

For a 10-12 month contract monitoring Colombian elections plus potential expansion to other countries:

| Phase | Estimated Volume | Sources | Concurrent Users |
|-------|-----------------|---------|-----------------|
| Demo (now) | ~5K-20K posts | 3-4 sources, 1 country | 1-3 developers |
| Pilot (M1-3) | ~50K-200K posts | 5-6 sources, 1-2 countries | 3-5 team members |
| Production (M4-10) | ~500K-2M+ posts | 6+ sources, multiple countries | 5-10 analysts |
| Handover (M11-12) | Stable, maintenance mode | Same | CIVICUS staff |

### Scalability Path

DuckDB is designed for single-machine analytical workloads. As the project grows, the natural upgrade path preserves all existing SQL queries and Parquet data:

```
Demo            Pilot              Production           Enterprise
DuckDB -------> DuckDB/MotherDuck -> PostgreSQL+TimescaleDB -> BigQuery (serverless)
(embedded)      (cloud-shared)      (multi-user, time-series) (CIVICUS-managed)
     \                                    /
      `-------> All stages read/write Parquet --------'
```

| Scale Level | Solution | Migration Effort | When to Consider |
|------------|----------|-----------------|-----------------|
| Single analyst, < 10M rows | **DuckDB** (current) | N/A | Demo and early pilot |
| Multiple analysts, shared access | **MotherDuck** (cloud DuckDB) | Minimal — same SQL, add connection string | When CIVICUS team needs simultaneous access |
| Heavy time-series, concurrent dashboards | **PostgreSQL + TimescaleDB** | Moderate — SQL is compatible, schema migrates directly | When real-time dashboards serve multiple teams |
| Serverless, no infrastructure management | **BigQuery** | Moderate — Parquet upload, SQL dialect differences | If CIVICUS prefers fully managed cloud (already used for GDELT) |
| Columnar analytics at scale | **ClickHouse** | Moderate — SQL-compatible, optimized for INSERT-heavy workloads | If write volume exceeds PostgreSQL comfort zone |

### Key Design Decision

The Parquet-based data layer convention (01_raw through 06_reporting) ensures **zero vendor lock-in**. Every database option above can read Parquet natively. The actual production choice should be made during the Inception Phase (M1-2) based on:

- CIVICUS's existing cloud infrastructure (AWS, GCP, Azure?)
- Number of concurrent users expected
- Whether real-time dashboards are needed vs. batch analysis
- CIVICUS's internal technical capacity for database administration
- Budget constraints for managed services

This decision is explicitly deferred to the Inception Report (Deliverable 1), where the team will recommend a production storage strategy based on CIVICUS's actual requirements and constraints.
