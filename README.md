# Pulso Electoral Colombia 2026

**Social listening and NLP for electoral discourse analysis -- built as a capability demonstration for the CIVICUS Digital Democracy Initiative.**

Colombia's 2026 election cycle is unfolding under conditions of rising polarization, coordinated digital manipulation, and threats to civic space. Monitoring how these dynamics play out in online discourse requires social listening infrastructure that works with Latin American Spanish, handles the nuances of Colombian political culture, and produces research-grade outputs -- not marketing dashboards.

This project demonstrates that capability. Built in approximately one week, it collects live data from four sources, processes it through NLP models trained on Latin American Spanish, and delivers reproducible analytical notebooks that follow a Signal-Insight-Action-Outcome framework designed for research teams.

---

## What This Demo Demonstrates

Everything here is real and running -- not mockups, not planned features.

| What is working | What it produces |
|-----------------|------------------|
| 4-source data pipeline (RSS, Reddit, GDELT, ACLED) | Normalized, deduplicated datasets across news, social media, and event databases |
| Sentiment analysis with `pysentimiento` | Polarity and emotion scores calibrated to Latin American Spanish (trained on ~500M tweets) |
| Named entity recognition with `spaCy` | Politicians, organizations, and locations extracted from Spanish text |
| Topic modeling with sentence-transformers | Emerging narrative clusters detected without predefined categories |
| 10 numbered notebooks across 5 stages | Reproducible analytical story from raw data to findings |
| Config-driven keyword monitoring | 5 YAML configs: election, manipulation, civic space, political figures, Colombian slang |
| Tool comparison analysis | Brandwatch vs. open-source evaluation with cost, language, and sustainability criteria |
| Signal-Insight-Action-Outcome templates | Structured handoff format between data analyst and domain expert |
| Data ethics and compliance documentation | Reddit API compliance, data minimization, no-model-training policy |
| Zero-cost infrastructure | All sources free, storage embedded (DuckDB), runs on a laptop |

---

## Capability-to-Engagement Mapping

Each capability demonstrated here enables a specific part of the DDI consulting engagement. This table maps what the demo proves to what it means for the actual work.

| Demonstrated capability | What this enables in a full engagement |
|-------------------------|----------------------------------------|
| Multi-source collection pipeline | Rapid onboarding of additional sources (Telegram, Bluesky, X) -- each new source is one fetch function and one normalize function; downstream analysis does not change |
| Latin American Spanish NLP | Accurate sentiment and emotion detection for Colombian discourse, extensible to other Global South languages via AfriSenti and XLM-RoBERTa |
| Config-driven keyword system | Non-technical team members adjust monitoring scope by editing YAML files, no code changes required |
| Colombian political slang normalization | Culturally-aware preprocessing that captures terms like *bodega* (troll farm), *mermelada* (patronage), and *castrochavismo* (polarization signal) -- missed by generic Spanish models |
| ACLED + GDELT integration | Cross-referencing online sentiment with real-world protest, violence, and political events for early warning detection |
| Reproducible notebook workflow | Every analytical claim is auditable, re-runnable, and documented -- critical for research credibility and funder reporting |
| DuckDB embedded storage | Zero-infrastructure deployment; migrates to MotherDuck (cloud), PostgreSQL, or BigQuery when team size and access needs require it |
| Open-source stack at $0/year | Sustainable after contract ends -- CIVICUS keeps everything, no license expiration |

---

## Thematic Coverage

The CIVICUS DDI Terms of Reference identify three thematic areas. Here is what this demo covers for each and how a funded engagement would extend it.

| ToR thematic area | What is demonstrated here | How we would apply it in the engagement |
|-------------------|---------------------------|----------------------------------------|
| **Algorithmic Bias and Polarisation** | Sentiment distribution by platform; Colombian slang configs that flag polarization signals (*mamerto*, *paraco*, *tibio*); cross-source comparison of tone | Longitudinal narrative tracking, visibility asymmetry analysis across platforms, coordinated amplification detection |
| **Digital Manipulation During Elections** | Keyword configs for *bodegas digitales*, *cuentas falsas*, *granjas de trolls*; hate speech detection via pysentimiento; topic clustering that surfaces emerging manipulation narratives | Network analysis with coordination detection (NetworkX + Louvain), bot scoring heuristics, real-time alerting on anomalous narrative velocity |
| **Early Warning Indicators** | ACLED event data correlated with online sentiment shifts; Signal-Insight-Action-Outcome framework for structured analytical handoff | Anomaly detection on narrative velocity, automated threshold alerts, ACLED + GDELT + social media triangulation for early warning dashboards |

---

## Demo vs. Full Engagement

This demo is a proof of concept, not a finished product. Here is what changes with funding and a proper engagement timeline.

| Dimension | This demo | A funded engagement adds |
|-----------|-----------|--------------------------|
| **Data sources** | 4 (RSS, Reddit, GDELT, ACLED) | Telegram, Bluesky, X/Twitter, Facebook (via CrowdTangle or equivalent) |
| **Collection mode** | Manual notebook runs | Automated scheduled collection (cron/Airflow) |
| **Analysis depth** | Sentiment, NER, topic clustering | Network analysis, coordination detection, visibility asymmetry, bot scoring |
| **Geographic scope** | Colombia only | Multi-country (methodology portable via config changes and model swaps) |
| **NLP languages** | Latin American Spanish | Additional Global South languages via AfriSenti, XLM-RoBERTa, NLLB |
| **Storage** | Local DuckDB file | Cloud-accessible database (MotherDuck, PostgreSQL, or BigQuery -- decided in Inception Phase) |
| **Team** | Solo data engineer | Data engineer + domain expert + research coordinator |
| **Outputs** | Notebooks + exported CSVs | Research Data Packages (dataset + insight brief + visualizations + methodology note) |
| **Training** | Documentation only | Live capacity building sessions, recorded training, advisory support |
| **Dashboard** | Prototype Streamlit app | Production monitoring dashboard with role-based access |

---

## Data Governance and Ethics

Research-grade social listening requires explicit data governance. This project includes both documentation and implementation.

- **Data ethics framework**: [`docs/data_ethics.md`](docs/data_ethics.md) -- covers Reddit API compliance (Responsible Builder Policy), rate limiting, data minimization, no-model-training commitment, and source-specific compliance notes for GDELT and ACLED
- **Tool comparison**: [`notebooks/5-appendix/01_mgo_tool_comparison_20260328.ipynb`](notebooks/5-appendix/01_mgo_tool_comparison_20260328.ipynb) -- evaluates Brandwatch, Meltwater, Talkwalker, and Pulsar against the open-source stack on cost, Latin American language support, data ownership, reproducibility, capacity building, and sustainability
- **General principles**: minimum necessary collection, no re-identification, local storage by default, purpose limitation, credentials never committed

The tool comparison concludes that for DDI's specific needs (Global South languages, research reproducibility, capacity building, sustainability after contract), an open-source stack provides superior value -- at $0/year vs. $10K-180K/year for commercial alternatives.

---

## Architecture

```
conf/ (YAML configs)
  |   keywords/*.yml (election, manipulation, civic_space, political_figures, slang)
  |   data_collection/, nlp/
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

## Data Sources

| # | Source | What you get | Library |
|---|--------|-------------|---------|
| 1 | Colombian RSS Feeds | News articles from major outlets | `feedparser` |
| 2 | Reddit r/Colombia | Political discussion (500-700K members) | `praw` |
| 3 | GDELT | Colombian news events, tone, themes | `requests` |
| 4 | ACLED | Protests, political violence, social leader killings | `requests` |

**Total infrastructure cost: $0** -- all sources are free or open-access.

### RSS Feed Availability as a Research Finding

Of eleven originally targeted Colombian news outlets, only five currently provide public RSS feeds: El Tiempo (Colombia and Politics sections), La Silla Vacía, Razón Pública, and Pulzo. The remaining six have discontinued public RSS entirely with no working alternatives:

| Outlet | Notes |
|--------|-------|
| El Espectador | Oldest newspaper in Colombia; independent editorial line |
| Semana | Major news magazine; historically center-right |
| Cambio Colombia | Investigative journalism |
| Caracol Radio | Major radio network with online presence |
| Blu Radio | Second-largest radio network |

This is not merely a data collection inconvenience. When major outlets close machine-readable data channels, the pool of sources accessible to independent monitors concentrates around those that still offer open feeds. Reduced plurality in accessible sources limits monitoring coverage and raises the barrier for civil society organizations without commercial data subscriptions. This dynamic is directly relevant to civic space health and is documented here as a methodological finding.

This situation reinforces the project's multi-source design: RSS alone cannot provide adequate coverage of the Colombian media landscape, which is why GDELT, ACLED, and Reddit are treated as co-equal primary sources rather than supplements.

## Notebook Guide

| Stage | Notebooks | Purpose |
|-------|-----------|---------|
| **1-data** | 3 collection notebooks | Collect from RSS, Reddit, GDELT+ACLED |
| **2-exploration** | 1 overview notebook | EDA, platform comparison, data quality |
| **3-analysis** | 3 analysis notebooks | Sentiment, NER, topic modeling |
| **4-output** | 2 output notebooks | Dataset export + analysis summary (Signal-Insight-Action-Outcome framework) |
| **5-appendix** | 1 comparison notebook | Brandwatch vs. open-source tool evaluation |

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
