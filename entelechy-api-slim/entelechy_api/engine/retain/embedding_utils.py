"""
Embedding generation utilities for memory units.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


def generate_embedding(embeddings_backend, text: str) -> list[float]:
    """
    Generate embedding for text using the provided embeddings backend.

    Args:
        embeddings_backend: Embeddings instance to use for encoding
        text: Text to embed

    Returns:
        Embedding vector (dimension depends on embeddings backend)
    """
    try:
        embeddings = embeddings_backend.encode([text])
        return embeddings[0]
    except Exception as e:
        raise Exception(f"Failed to generate embedding: {str(e)}")


async def generate_embeddings_batch(embeddings_backend, texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts using the provided embeddings backend.

    Runs the embedding generation in a thread pool to avoid blocking the event loop
    for CPU-bound operations.

    Args:
        embeddings_backend: Embeddings instance to use for encoding
        texts: List of texts to embed

    Returns:
        List of embeddings in same order as input texts
    """
    try:
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            embeddings_backend.encode,
            texts,
        )
    except Exception as e:
        raise Exception(f"Failed to generate batch embeddings: {str(e)}")

    # Guarantee 1:1 alignment with input texts. A silent length mismatch here
    # propagates downstream as zip() drops items, eventually surfacing as an
    # IndexError in retain mapping (see issue #1037).
    if len(embeddings) != len(texts):
        raise RuntimeError(
            f"Embeddings backend returned {len(embeddings)} vectors for {len(texts)} input texts; "
            "expected exact 1:1 alignment"
        )

    return embeddings


async def generate_query_embeddings_batch(embeddings_backend, texts: list[str]) -> list[list[float]]:
    """
    Embed search queries. Uses the backend's query mode (asymmetric models such as
    NVIDIA's distinguish query from passage); otherwise identical to the passage path.
    """
    encode = getattr(embeddings_backend, "encode_query", None) or embeddings_backend.encode
    try:
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, encode, texts)
    except Exception as e:
        raise Exception(f"Failed to generate query embeddings: {str(e)}")
    if len(embeddings) != len(texts):
        raise RuntimeError(f"Embeddings backend returned {len(embeddings)} vectors for {len(texts)} queries")
    return embeddings
