"""Named entity extraction using spaCy."""

from __future__ import annotations

import spacy

# Lazy loading — model loaded on first call
_nlp_model: spacy.language.Language | None = None


def get_nlp_model(model_name: str = "es_core_news_lg") -> spacy.language.Language:
    """Get or load a spaCy NLP model.

    Parameters
    ----------
    model_name : str
        spaCy model name. Defaults to 'es_core_news_lg'.

    Returns
    -------
    spacy.language.Language
        Loaded spaCy model.
    """
    global _nlp_model  # noqa: PLW0603
    if _nlp_model is None:
        _nlp_model = spacy.load(model_name)
    return _nlp_model


def extract_entities(texts: list[str]) -> list[dict]:
    """Extract named entities from a list of texts.

    Parameters
    ----------
    texts : list[str]
        List of text strings to process.

    Returns
    -------
    list[dict]
        List of dicts with keys: text (original), entities (list of entity dicts
        with 'text', 'label', 'start', 'end').
    """
    nlp = get_nlp_model()
    results = []
    for doc in nlp.pipe(texts, batch_size=50):
        entities = [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            }
            for ent in doc.ents
        ]
        results.append({"text": doc.text, "entities": entities})
    return results


def extract_persons(texts: list[str]) -> list[list[str]]:
    """Extract person names from a list of texts.

    Parameters
    ----------
    texts : list[str]
        List of text strings to process.

    Returns
    -------
    list[list[str]]
        List of lists of person name strings, one per input text.
    """
    nlp = get_nlp_model()
    results = []
    for doc in nlp.pipe(texts, batch_size=50):
        persons = [ent.text for ent in doc.ents if ent.label_ == "PER"]
        results.append(persons)
    return results
