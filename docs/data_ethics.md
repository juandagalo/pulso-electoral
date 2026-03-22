# Data Ethics & Compliance

This document describes how Pulso Electoral handles data from each collection source, with particular focus on Reddit's Responsible Builder Policy, data minimization, and research boundaries.

---

## Reddit Data Usage & Compliance

### API Access

Data is collected exclusively via Reddit's official API using [PRAW](https://praw.readthedocs.io/) (Python Reddit API Wrapper). The project is registered as a Reddit application with:

- An accurate description of the project's research purpose
- A user agent string that identifies the project and developer (e.g., `pulso-electoral:v0.1 by u/<developer>`)
- Credentials stored locally in `.env` — never committed to version control

We comply with Reddit's [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki) and the [Reddit API Terms of Service](https://www.reddit.com/wiki/api).

### Rate Limiting

PRAW handles Reddit's rate limits automatically (100 requests/minute). Our collection scope — approximately 300 posts per run from `r/Colombia` across three sort modes (`hot`, `new`, `top`) — is well within acceptable usage and does not require any custom throttling beyond PRAW's built-in handling.

| Parameter | Value |
|-----------|-------|
| Target subreddit | r/Colombia |
| Sort modes | hot, new, top |
| Max posts per sort | 100 |
| Approximate posts per run | ~300 |
| PRAW rate limit | 100 requests/minute (auto-managed) |

### No Model Training on Reddit Data

We use pre-trained models for all NLP tasks — inference only:

| Task | Model | Source |
|------|-------|--------|
| Sentiment analysis | `pysentimiento/robertuito-sentiment-analysis` | HuggingFace |
| Emotion detection | `pysentimiento/robertuito-emotion-analysis` | HuggingFace |
| Hate speech detection | `pysentimiento/robertuito-hate-speech` | HuggingFace |
| Named entity recognition | `spaCy es_core_news_lg` | spaCy |
| Topic modeling | sentence-transformers + sklearn (`paraphrase-multilingual-MiniLM-L12-v2`) | HuggingFace |

We do **not** train or fine-tune any model on Reddit data. Doing so would require explicit written approval from Reddit under their Responsible Builder Policy. All models were trained on publicly available, independently licensed corpora before this project began.

### No Commercialization

Reddit data collected by this project is used strictly for academic and research demonstration purposes in support of the CIVICUS Digital Democracy Initiative application. Specifically:

- Raw Reddit data is **not redistributed**, sold, or licensed to third parties
- Collected data is **not used** to build commercial products or services
- Aggregated findings (e.g., sentiment trend charts) may be shared in reports to CIVICUS, but these do not expose individual post content at scale

### Data Minimization

Collection is scoped to the minimum data necessary for electoral discourse analysis:

- Only **public** posts and top-level comments are collected (no private messages, no user account data beyond post author handle)
- Filtered to `r/Colombia` with political flairs (`Politica`, `Noticias`, `Opinion`, `Elecciones`) and election-related keywords
- No historical bulk downloads — collection runs in bounded daily batches
- Raw files are stored locally in `data/01_raw/reddit/` and are not uploaded to any external service

### Transparency

| Requirement | Implementation |
|-------------|---------------|
| Registered application | Yes — Reddit Developer Portal with accurate project description |
| User agent identification | `REDDIT_USER_AGENT` env var, defaults to `pulso-electoral:v0.1` |
| Credentials | Stored in `.env` (not committed), rotated if exposed |
| Rate limit compliance | PRAW automatic (100 req/min) |
| Data retention | Local only; raw files in `data/01_raw/reddit/` |
| Model training on Reddit data | No — inference only using pre-trained models |

---

## Other Data Sources

| Source | Key Compliance Notes |
|--------|---------------------|
| Colombian RSS Feeds | Public news syndication feeds; no authentication required; standard fair-use access |
| GDELT Project | Open data released into the public domain by Google; no usage restrictions |
| ACLED | Free for non-commercial research use under [ACLED Terms](https://acleddata.com/terms-of-use/); data not redistributed |

---

## General Research Data Principles

1. **Minimum necessary collection** — collect only the fields and volume required for the analysis task
2. **No re-identification** — analysis targets aggregate discourse patterns, not individual users
3. **Local storage by default** — raw data stays on the researcher's machine; no third-party cloud uploads unless explicitly configured
4. **Credentials never committed** — all API keys and secrets are stored in `.env`, which is listed in `.gitignore`
5. **Purpose limitation** — data collected for electoral discourse research is not repurposed for unrelated tasks

---

## References

- Reddit Responsible Builder Policy: https://support.reddithelp.com/hc/en-us/articles/16160319875092
- Reddit API Terms of Service: https://www.reddit.com/wiki/api
- PRAW documentation: https://praw.readthedocs.io/
- ACLED Terms of Use: https://acleddata.com/terms-of-use/
- pysentimiento: https://github.com/pysentimiento/pysentimiento
