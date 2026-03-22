"""Sentiment analysis using pysentimiento."""

from __future__ import annotations

from pysentimiento import create_analyzer

# Lazy loading — models loaded on first call
_analyzers: dict = {}


def get_analyzer(task: str = "sentiment", lang: str = "es") -> object:
    """Get or create a pysentimiento analyzer.

    Parameters
    ----------
    task : str
        Analysis task: 'sentiment', 'emotion', 'hate_speech', 'irony'.
    lang : str
        Language code. Defaults to 'es' for Spanish.

    Returns
    -------
    object
        A pysentimiento analyzer instance.
    """
    key = f"{task}_{lang}"
    if key not in _analyzers:
        _analyzers[key] = create_analyzer(task=task, lang=lang)
    return _analyzers[key]


def analyze_sentiment(texts: list[str]) -> list[dict]:
    """Run sentiment analysis on a list of texts.

    Parameters
    ----------
    texts : list[str]
        List of text strings to analyze.

    Returns
    -------
    list[dict]
        List of dicts with keys: label, probas.
    """
    analyzer = get_analyzer("sentiment")
    return [
        {"label": r.output, "probas": r.probas}
        for r in [analyzer.predict(t) for t in texts]  # type: ignore[union-attr]
    ]


def analyze_emotion(texts: list[str]) -> list[dict]:
    """Run emotion analysis on a list of texts.

    Parameters
    ----------
    texts : list[str]
        List of text strings to analyze.

    Returns
    -------
    list[dict]
        List of dicts with keys: label, probas.
    """
    analyzer = get_analyzer("emotion")
    return [
        {"label": r.output, "probas": r.probas}
        for r in [analyzer.predict(t) for t in texts]  # type: ignore[union-attr]
    ]


def analyze_hate_speech(texts: list[str]) -> list[dict]:
    """Run hate speech detection on a list of texts.

    Parameters
    ----------
    texts : list[str]
        List of text strings to analyze.

    Returns
    -------
    list[dict]
        List of dicts with keys: label, probas.
    """
    analyzer = get_analyzer("hate_speech")
    return [
        {"label": r.output, "probas": r.probas}
        for r in [analyzer.predict(t) for t in texts]  # type: ignore[union-attr]
    ]
