# Data Ethics & Compliance

This document describes how Pulso Electoral handles data from each collection source, with particular focus on data minimization and research boundaries.

---

## Data Sources & Compliance

| Source | Key Compliance Notes |
|--------|---------------------|
| Colombian RSS Feeds | Public news syndication feeds; no authentication required; standard fair-use access |
| GDELT Project | Open data released into the public domain by Google; no usage restrictions |
| ACLED | Free for non-commercial research use under [ACLED Terms](https://acleddata.com/terms-of-use/); data not redistributed |

> **Note on Reddit**: Reddit was initially planned as a social media data source (r/Colombia) but was deferred due to API access delays. The architecture supports adding it back when API access is granted. If Reddit is re-added in a future engagement, the project will comply with Reddit's [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki) and API Terms of Service.

---

## NLP Models -- Inference Only

We use pre-trained models for all NLP tasks -- inference only:

| Task | Model | Source |
|------|-------|--------|
| Sentiment analysis | `pysentimiento/robertuito-sentiment-analysis` | HuggingFace |
| Emotion detection | `pysentimiento/robertuito-emotion-analysis` | HuggingFace |
| Hate speech detection | `pysentimiento/robertuito-hate-speech` | HuggingFace |
| Named entity recognition | `spaCy es_core_news_lg` | spaCy |
| Topic modeling | sentence-transformers + sklearn (`paraphrase-multilingual-MiniLM-L12-v2`) | HuggingFace |

We do **not** train or fine-tune any model on collected data. All models were trained on publicly available, independently licensed corpora before this project began.

---

## General Research Data Principles

1. **Minimum necessary collection** -- collect only the fields and volume required for the analysis task
2. **No re-identification** -- analysis targets aggregate discourse patterns, not individual users
3. **Local storage by default** -- raw data stays on the researcher's machine; no third-party cloud uploads unless explicitly configured
4. **Credentials never committed** -- all API keys and secrets are stored in `.env`, which is listed in `.gitignore`
5. **Purpose limitation** -- data collected for electoral discourse research is not repurposed for unrelated tasks

---

## References

- ACLED Terms of Use: https://acleddata.com/terms-of-use/
- pysentimiento: https://github.com/pysentimiento/pysentimiento
