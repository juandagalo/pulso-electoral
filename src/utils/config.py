"""Configuration loading utilities using yaml.safe_load()."""

from __future__ import annotations

from pathlib import Path

import yaml


def load_config(path: str | Path) -> dict:
    """Load a YAML configuration file.

    Parameters
    ----------
    path : str | Path
        Path to the YAML file.

    Returns
    -------
    dict
        Parsed YAML content as a dictionary.

    Raises
    ------
    FileNotFoundError
        If the config file does not exist.
    yaml.YAMLError
        If the YAML content is malformed.
    """
    path = Path(path)
    if not path.exists():
        msg = f"Configuration file not found: {path}"
        raise FileNotFoundError(msg)
    with open(path) as f:
        return yaml.safe_load(f)


def load_keywords(category: str, conf_dir: str | Path = "conf/keywords") -> list[str]:
    """Load keywords from a specific category YAML file.

    Parameters
    ----------
    category : str
        Keyword category name (e.g., 'election', 'manipulation', 'civic_space').
    conf_dir : str | Path
        Directory containing keyword YAML files.

    Returns
    -------
    list[str]
        List of keywords for the given category.
    """
    config = load_config(Path(conf_dir) / f"{category}.yml")
    return config.get("keywords", [])


def load_all_keywords(conf_dir: str | Path = "conf/keywords") -> dict[str, list[str]]:
    """Load all keyword categories from the keywords config directory.

    Parameters
    ----------
    conf_dir : str | Path
        Directory containing keyword YAML files.

    Returns
    -------
    dict[str, list[str]]
        Dictionary mapping category names to keyword lists.
    """
    conf_dir = Path(conf_dir)
    categories = {}
    for yml_file in conf_dir.glob("*.yml"):
        config = load_config(yml_file)
        categories[yml_file.stem] = config.get("keywords", [])
    return categories
