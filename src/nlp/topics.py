"""Topic modeling utilities using sentence-transformers embeddings.

NOTE: BERTopic was removed as a dependency. This module provides embedding-based
helpers only. Full topic modeling (clustering + labeling) is implemented directly
in the analysis notebook using sentence-transformers + sklearn.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def compute_embeddings(
    texts: list[str],
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
) -> NDArray[np.float32]:
    """Compute sentence embeddings for a list of texts.

    Parameters
    ----------
    texts : list[str]
        List of text strings to embed.
    model_name : str
        Sentence-transformers model name. Defaults to multilingual MiniLM.

    Returns
    -------
    NDArray[np.float32]
        2-D array of shape (len(texts), embedding_dim).
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    embeddings: NDArray[np.float32] = model.encode(texts, show_progress_bar=False)
    return embeddings
