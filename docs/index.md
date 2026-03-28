# Pulso Electoral Colombia 2026

**Social listening and NLP for electoral discourse analysis -- built as a capability demonstration for the CIVICUS Digital Democracy Initiative.**

Colombia's 2026 election cycle is unfolding under conditions of rising polarization, coordinated digital manipulation, and threats to civic space. Monitoring how these dynamics play out in online discourse requires social listening infrastructure that works with Latin American Spanish, handles the nuances of Colombian political culture, and produces research-grade outputs -- not marketing dashboards.

This project demonstrates that capability.

## Quick Links

- [Architecture](architecture.md) -- design philosophy, data layers, and project structure
- [Data Ethics](data_ethics.md) -- compliance, minimization, and ethical guidelines
- [PRD](PRD.md) -- product requirements document

## What This Demo Demonstrates

| What is working | What it produces |
|-----------------|------------------|
| 3-source data pipeline (RSS, GDELT, ACLED) | Normalized, deduplicated datasets across news and event databases |
| Sentiment analysis with `pysentimiento` | Polarity and emotion scores calibrated to Latin American Spanish |
| Named entity recognition with `spaCy` | Politicians, organizations, and locations extracted from Spanish text |
| Topic modeling with sentence-transformers | Emerging narrative clusters detected without predefined categories |
| 10 numbered notebooks across 5 stages | Reproducible analytical story from raw data to findings |
| Config-driven keyword monitoring | 5 YAML configs: election, manipulation, civic space, political figures, Colombian slang |
| Zero-cost infrastructure | All sources free, storage embedded (DuckDB), runs on a laptop |
