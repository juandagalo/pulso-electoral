"""Text preprocessing utilities for Colombian Spanish."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Colombian slang normalizations loaded from config
_slang_map: dict[str, str] | None = None


def _load_slang_map(
    config_path: str | Path = "conf/keywords/slang.yml",
) -> dict[str, str]:
    """Load slang normalization mapping from YAML config.

    Parameters
    ----------
    config_path : str | Path
        Path to slang YAML file.

    Returns
    -------
    dict[str, str]
        Mapping of slang terms to their normalizations.
    """
    global _slang_map  # noqa: PLW0603
    if _slang_map is None:
        path = Path(config_path)
        if path.exists():
            with open(path) as f:
                config = yaml.safe_load(f)
            _slang_map = config.get("normalizations", {})
        else:
            _slang_map = {}
    return _slang_map


def normalize_colombian_text(text: str) -> str:
    """Normalize Colombian slang in text while preserving structure.

    Replaces Colombian slang terms with their standard Spanish equivalents
    for better NLP model performance. The original text should be preserved
    separately for audit trail.

    Parameters
    ----------
    text : str
        Input text that may contain Colombian slang.

    Returns
    -------
    str
        Text with slang replaced by standard equivalents.
    """
    slang_map = _load_slang_map()
    normalized = text
    for slang, replacement in slang_map.items():
        pattern = re.compile(rf"\b{re.escape(slang)}\b", re.IGNORECASE)
        normalized = pattern.sub(replacement, normalized)
    # Clean up multiple spaces from removals
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def clean_text(text: str) -> str:
    """Clean text for NLP processing.

    Removes URLs, mentions, excessive whitespace, and normalizes unicode.

    Parameters
    ----------
    text : str
        Raw text to clean.

    Returns
    -------
    str
        Cleaned text ready for NLP processing.
    """
    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove @mentions
    text = re.sub(r"@\w+", "", text)
    # Remove multiple spaces, tabs, newlines
    text = re.sub(r"\s+", " ", text)
    # Strip leading/trailing whitespace
    return text.strip()


def detect_language(text: str) -> tuple[str, float]:
    """Detect the language of a text string.

    Parameters
    ----------
    text : str
        Text to detect language for.

    Returns
    -------
    tuple[str, float]
        Language code (e.g., 'es') and confidence score.
    """
    from langdetect import detect_langs

    try:
        results = detect_langs(text)
        if results:
            return results[0].lang, results[0].prob
    except Exception:
        logger.debug("Language detection failed for text: %.50s...", text, exc_info=True)
    return "unknown", 0.0
