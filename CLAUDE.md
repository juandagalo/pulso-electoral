# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Pulso Electoral Colombia 2026** is a research-oriented social listening project that monitors digital manipulation and civic space health during Colombia's 2026 election cycle. Built as the primary technical work sample for a consulting application to the CIVICUS Digital Democracy Initiative.

This is a **research project, NOT a software product**. Notebooks are the primary deliverables. The `src/` directory contains thin, reusable utility functions consumed by notebooks.

## Essential Commands

### Environment Setup
- `make install_env` - Install dependencies and pre-commit hooks (run after cloning)
- `make download_models` - Download spaCy es_core_news_lg model
- `uv add <package>` - Add new production dependency
- `uv add --group dev <package>` - Add development dependency
- `make clean_env` - Remove `.venv` virtual environment

### Data Collection
- `make collect_rss` - Run RSS collection notebook
- `make collect_reddit` - Run Reddit collection notebook
- `make collect_gdelt_acled` - Run GDELT + ACLED collection notebook
- `make collect_all` - Run all collection notebooks sequentially
- `make analyze` - Run all analysis notebooks (sentiment, NER, topics)
- `make export` - Run output notebooks (dataset export + analysis summary)

### Testing & Quality
- `make test` - Run pytest with coverage report
- `make test_verbose` - Run pytest with verbose output
- `make check` - Run all pre-commit hooks (ruff, mypy, commitizen)
- `make lint` - Run ruff only (faster than `make check`)
- `uv run pytest tests/<file>.py::<test_name>` - Run single test

### Application
- `make run_app` - Start Streamlit dashboard at localhost:8501

### Documentation
- `make docs` - Serve documentation locally with MkDocs
- `make docs_test` - Build docs to check for errors

## Architecture

This project follows a research-first architecture:

```
conf/ (YAML configs)          --> loaded with yaml.safe_load() — NO Pydantic
    |
    v
notebooks/ (PRIMARY output)   --> tell the story: collection, analysis, findings
    |
    v
src/ (thin utilities)         --> simple helpers consumed by notebooks
    |
    v
data/ (numbered layers)       --> 01_raw -> 02_intermediate -> ... -> 06_reporting
    |
    v
app/ (optional Streamlit)     --> lightweight interactive exploration tool
```

### Key Design Decisions

1. **Notebooks are the primary deliverables** — they tell the story for CIVICUS reviewers
2. **src/ contains THIN utilities** — simple functions under 50 lines, no abstract classes, no inheritance
3. **HuggingFace models used directly** — `pysentimiento.create_analyzer()` in notebooks, not wrapped in classes
4. **conf/ uses simple YAML** — loaded with `yaml.safe_load()`, no Pydantic settings system
5. **DuckDB for storage** — zero-infrastructure analytical database, single file

### Storage

- **DuckDB** is used as the embedded analytical storage engine (zero-infrastructure, single file)
- Data is also stored as **Parquet files** in the numbered data layers (`01_raw` through `06_reporting`), ensuring portability and zero vendor lock-in
- The **production database decision is deferred** to the contract Inception Phase (Deliverable 1), when CIVICUS's actual infrastructure, user count, and budget constraints are known
- All database helpers live in `src/storage/db.py`

### Data Layer Convention

Data flows through numbered layers in `data/` — never write back to an earlier layer:

| Layer | Purpose |
|---|---|
| `01_raw` | Immutable collected data (JSON/CSV per source per day) |
| `02_intermediate` | Normalized to common schema |
| `03_primary` | Cleaned, deduplicated, language-filtered |
| `04_enriched` | NLP results added (sentiment, NER, topics) |
| `05_analysis` | Aggregated analysis results |
| `06_reporting` | Final outputs for data packages |

### Notebooks

Notebooks in `notebooks/` follow a numbered workflow stage:
`1-data` -> `2-exploration` -> `3-analysis` -> `4-output` -> `5-appendix`

**Naming convention:** `{consecutive}_{mgo}_{nameOfTheNotebook}_{YYYYMMDD}.ipynb`
- `consecutive`: zero-padded sequential number within the subfolder (e.g., `01`, `02`)
- `mgo`: fixed author initials, always literal
- `nameOfTheNotebook`: short `snake_case` description
- `YYYYMMDD`: creation date

Use `notebooks/notebook_template.ipynb` as the starting point for new notebooks. Notebooks must have emoji section headers.

### Configuration

`conf/` contains focused YAML config files split by domain:
- `conf/data_collection/` — feed URLs, channel lists, API filters
- `conf/keywords/` — keyword lists by category (election, manipulation, civic space)
- `conf/nlp/` — model names, tasks, languages

All loaded with `yaml.safe_load()` via `src/utils/config.py`.

## Code Quality Standards

### Key Rules
- **All functions must have type annotations** — mypy enforces `disallow_untyped_defs` and `disallow_untyped_calls`
- **`from __future__ import annotations`** — required in ALL Python files
- **Commits must follow Conventional Commits** — commitizen hook enforces this
- **Tests mirror `src/` structure**: `src/collectors/rss.py` -> `tests/collectors/test_rss.py`
- **`assert` statements (S101) are allowed in tests**

### Ruff (`.code_quality/ruff.toml`)
- Line length: 100, double quotes, max complexity: 10, target Python 3.12
- Applies to `.ipynb` notebooks as well
- Pre-commit runs both `ruff` (lint + auto-fix) and `ruff-format`

### MyPy (`.code_quality/mypy.ini`)
- Strict: `disallow_untyped_defs`, `disallow_untyped_calls`, `ignore_missing_imports: True`

## Tech Stack

| Category | Tool |
|----------|------|
| Language | Python 3.12 |
| Package Manager | uv |
| NLP - Sentiment | pysentimiento (Latin American Spanish) |
| NLP - NER | spaCy es_core_news_lg |
| NLP - Topics | sentence-transformers + sklearn |
| Collection | feedparser, praw, requests |
| Storage | DuckDB |
| Dashboard | Streamlit + Plotly + Folium |
| Config | PyYAML (yaml.safe_load) |
| CI | GitHub Actions |
| Containers | Docker |
