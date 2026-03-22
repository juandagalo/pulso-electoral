# Pulso Electoral Colombia 2026

**Social Listening & NLP for Electoral Discourse Analysis -- A Technical Demo**

Pulso Electoral is a working proof of concept that demonstrates social listening and multilingual NLP capabilities for monitoring electoral discourse and digital manipulation in Colombia's 2026 election cycle. It collects public discourse from Colombian news outlets, Reddit, and global event databases; processes it through NLP models trained on Latin American Spanish; detects narrative patterns; and presents findings as reproducible analytical notebooks.

Built as a capability demonstration for the [CIVICUS Digital Democracy Initiative](https://civicus.org) consulting application, this demo shows what a full engagement could look like -- with real data, real models, and a real pipeline running end to end.

---

## Architecture

```
conf/ (YAML configs)
  |   rss_feeds.yml, keywords/*.yml, models.yml
  |   loaded with yaml.safe_load() -- no Pydantic
  v
notebooks/ (PRIMARY deliverables)
  |   1-data/ --> 2-exploration/ --> 3-analysis/ --> 4-output/ --> 5-appendix/
  |   Each notebook tells a story: what data, how analyzed, what found
  v
src/ (thin utility functions)
  |   collectors/  nlp/  analysis/  storage/  utils/
  |   Simple helpers consumed by notebooks -- no abstract classes
  v
data/ (numbered layers)
  |   01_raw/ --> 02_intermediate/ --> 03_primary/ --> 04_enriched/ --> 05_analysis/ --> 06_reporting/
  v
app/ (optional Streamlit dashboard)
      Lightweight interactive exploration -- notebooks are the real output
```

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/pulso-electoral/pulso-electoral.git
cd pulso-electoral

# 2. Install dependencies (requires uv: https://docs.astral.sh/uv/)
make install_env

# 3. Copy environment variables and fill in API credentials
cp .env.example .env

# 4. Download NLP models
make download_models

# 5. Run collection notebooks
make collect_all

# 6. Run analysis notebooks
make analyze

# 7. Export datasets and analysis summary
make export

# 8. (Optional) Start the Streamlit dashboard
make run_app
```

## Data Sources

| # | Source | What You Get | Library |
|---|--------|-------------|---------|
| 1 | Colombian RSS Feeds | News articles from major outlets | `feedparser` |
| 2 | Reddit r/Colombia | Political discussion (500-700K members) | `praw` |
| 3 | GDELT | Colombian news events, tone, themes | `requests` |
| 4 | ACLED | Protests, political violence, social leader killings | `requests` |

**Total infrastructure cost: $0** -- all sources are free or open-access.

## Notebook Guide

| Stage | Notebooks | Purpose |
|-------|-----------|---------|
| **1-data** | 3 collection notebooks | Collect from RSS, Reddit, GDELT+ACLED |
| **2-exploration** | 1 overview notebook | EDA, platform comparison, data quality |
| **3-analysis** | 3 analysis notebooks | Sentiment, NER, topic modeling |
| **4-output** | 2 output notebooks | Dataset export + analysis summary for research team |
| **5-appendix** | 1 comparison notebook | Tool comparison (Brandwatch vs open-source) |

## Tech Stack

| Category | Tool |
|----------|------|
| Language | Python 3.12 |
| Package Manager | uv |
| NLP - Sentiment | pysentimiento (Latin American Spanish) |
| NLP - NER | spaCy es_core_news_lg |
| NLP - Topics | sentence-transformers + sklearn |
| Collection | feedparser, praw, requests |
| Storage | DuckDB (zero-infrastructure, single file) |
| Dashboard | Streamlit + Plotly + Folium |
| Config | PyYAML |
| CI | GitHub Actions |
| Containers | Docker |

### Why DuckDB?

- **Zero infrastructure**: Embedded analytical database -- no server setup, just a file
- **SQL on DataFrames**: Query collected data with standard SQL directly from pandas
- **Parquet native**: Reads/writes Parquet files, keeping data portable across tools
- **Scalable path**: Migrates cleanly to MotherDuck (cloud), PostgreSQL, or BigQuery for production

## Demonstrated Capabilities

This demo validates a set of core capabilities that translate directly into a full-scale engagement.

### What the demo proves

| Capability | How it works in this demo |
|------------|--------------------------|
| **Multi-source data collection** | 4 live sources (RSS, Reddit, GDELT, ACLED) collected through a uniform pipeline -- each source is one fetch function and one normalize function |
| **Multilingual NLP** | pysentimiento runs 4 models (sentiment, emotion, hate speech, irony) trained specifically on Latin American Spanish, not translated English |
| **Named entity recognition** | spaCy `es_core_news_lg` extracts politicians, organizations, and locations from Spanish-language text |
| **Topic and narrative detection** | sentence-transformers + sklearn KMeans cluster emerging narratives without predefined categories |
| **Reproducible research workflow** | Numbered notebooks tell a complete analytical story from raw data to findings, runnable with a single `make` command |
| **Zero-cost infrastructure** | All data sources are free, storage is embedded (DuckDB + Parquet), and the full pipeline runs on a laptop |

### How these scale in a real engagement

The architecture is designed so that scaling up means adding to the pipeline, not rebuilding it. Each additional data source requires one fetch function and one normalize function -- the downstream analysis does not change.

**Additional data sources** that slot into the existing pipeline:

| Source | Library | What it adds |
|--------|---------|-------------|
| Telegram channels | `telethon` | Encrypted messaging discourse (scoped to ~10 public channels) |
| Bluesky | `atproto` | Emerging social platform activity |

**Additional analytical layers** that build on the current NLP foundation:

- **Network analysis** -- coordination detection using NetworkX and Louvain community detection
- **Visibility asymmetry** -- cross-platform reach comparison to identify algorithmic amplification
- **Early warning indicators** -- anomaly detection on narrative velocity, correlated with ACLED physical events
- **Algorithmic bias and polarization** -- narrative tracking over time with cross-source sentiment comparison

DuckDB scales to MotherDuck (shared cloud access) or migrates to PostgreSQL/BigQuery with a connection-string change, not a rewrite. The production database choice would be finalized based on actual infrastructure and team size.

## Design Principles

The engineering choices behind this demo prioritize reproducibility and extensibility -- making it straightforward for another team to pick up, run, and build on.

- **Config-driven** -- keywords, sources, thresholds, and model names live in `conf/*.yml`. Monitoring scope can be adjusted without touching code.
- **Notebook workflow** -- analysis lives in numbered notebooks (`1-data` through `4-output`) that tell a research story, not black-box scripts. Each notebook is simultaneously documentation and executable code.
- **Makefile automation** -- `make collect_all`, `make analyze`, `make export` are the full operational interface. No Python knowledge required to run a collection cycle.
- **Portable data** -- Parquet files in `data/01_raw` through `data/06_reporting` are vendor-neutral and readable by any modern data tool.
- **Documentation** -- MkDocs site (`make docs`), architecture docs, and a data ethics framework are included.

## Development

```bash
make test           # Run tests with coverage
make check          # Run all pre-commit hooks (ruff, mypy, commitizen)
make lint           # Run ruff linter only
make docs           # Serve MkDocs documentation locally
```

## Team

This project was built for the CIVICUS Digital Democracy Initiative application, combining research expertise in Colombian political culture with data engineering and NLP capabilities.

## License

MIT
