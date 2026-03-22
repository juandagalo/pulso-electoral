# Pulso Electoral Colombia 2026

**Social Listening & Digital Manipulation Research for CIVICUS DDI**

Pulso Electoral is a research project that monitors digital manipulation and civic space health during Colombia's 2026 election cycle. It collects public discourse from Colombian news outlets, Reddit, and global event databases; processes it through multilingual NLP trained on Latin American Spanish; detects narrative anomalies; and presents findings as reproducible analytical notebooks.

This project serves as the primary technical work sample for a consulting application to the [CIVICUS Digital Democracy Initiative](https://civicus.org).

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

- **Zero infrastructure**: Embedded analytical database — no server setup, just a file
- **SQL on DataFrames**: Query collected data with standard SQL directly from pandas
- **Parquet native**: Reads/writes Parquet files, keeping data portable across tools
- **Scalable path**: Migrates cleanly to MotherDuck (cloud), PostgreSQL, or BigQuery for production

## 🚀 Scalability & Growth Path

### NLP Models

Each model is swappable via a single line in `conf/nlp/models.yml` — no code changes required.

| Component | Current | Upgrade Path |
|-----------|---------|--------------|
| Sentiment / Emotion / Hate / Irony | pysentimiento (robertuito, 4 models) | Any HuggingFace Spanish classifier — pysentimiento wraps the Transformers API |
| NER | spaCy `es_core_news_lg` | Transformer-based NER (e.g., `PlanTL-GOB-ES/roberta-base-bne-capitel-ner`) — change model name in config, `spacy-transformers` handles the rest |
| Topic embeddings | `paraphrase-multilingual-MiniLM-L12-v2` | Any sentence-transformers model — model name is a config value, embeddings are model-agnostic |
| Topic clustering | sklearn KMeans | HDBSCAN (density-based, no fixed k) or BERTopic — clustering runs on the same embeddings array |

### Data Sources

Current: 3 source families (RSS feeds, Reddit, GDELT+ACLED). Each collector follows the same pattern:

```
fetch raw data  →  normalize to common schema  →  write to data/01_raw/
```

Adding a new source means implementing one fetch function and one normalize function — no changes to the downstream pipeline.

| Potential source | Library | Status |
|-----------------|---------|--------|
| Telegram channels | `telethon` | Scoped (10 channels identified) |
| Bluesky | `atproto` | Scoped |
| Twitter/X | `tweepy` | Pending API access |

### Storage

| Phase | Solution | Trigger |
|-------|----------|---------|
| Demo (now) | **DuckDB** — embedded, zero infrastructure | < 10M rows, single analyst |
| Pilot | **MotherDuck** — cloud DuckDB, same SQL | CIVICUS team needs shared access |
| Production | **PostgreSQL** or **BigQuery** | Concurrent dashboards, multi-team |

Parquet files in `data/01_raw` through `data/06_reporting` are the interchange format. Every option above reads Parquet natively — migration is a connection-string change, not a rewrite. Production DB choice is deferred to the CIVICUS Inception Phase (Deliverable 1).

### Analysis Capabilities

| Layer | Current | Growth Path |
|-------|---------|-------------|
| Sentiment | Sentence-level (positive/negative/neutral) | Time-series sentiment velocity, cross-source comparison |
| NER | Persons, orgs, locations | Entity co-occurrence networks, entity-level sentiment |
| Topics | KMeans clusters on embeddings | Narrative tracking over time, cross-platform topic alignment |
| Network | — | Coordination detection (DBSCAN), community detection (Louvain/NetworkX) |
| Anomaly | — | Spike detection, narrative velocity alerts |
| Reporting | Manual notebook outputs | Automated Signal-Insight-Action-Outcome report generation |

### Infrastructure

- **CI** — GitHub Actions already runs on every push; add scheduled collection jobs with no infra changes
- **Docker** — `Dockerfile` is ready; deploy to any cloud run service (Cloud Run, ECS, Azure Container Apps)
- **Scheduling** — swap notebook `make` commands for cron, GitHub Actions schedules, or a cloud scheduler
- **GPU** — `sentence-transformers` and `pysentimiento` both support CUDA; set `device="cuda"` when volume justifies the cost

## Development

```bash
make test           # Run tests with coverage
make check          # Run all pre-commit hooks (ruff, mypy, commitizen)
make lint           # Run ruff linter only
make docs           # Serve MkDocs documentation locally
```

## Team

This project was developed for the CIVICUS Digital Democracy Initiative application, combining research expertise in Colombian political culture with data engineering capabilities.

## License

MIT
