"""
tools/vector_utils.py
---------------------
Small helpers for storing embeddings in pgvector columns.
"""


def to_pgvector_literal(embedding: list[float]) -> str:
    """Serialize an embedding to the text literal format accepted by pgvector."""
    return "[" + ",".join(str(x) for x in embedding) + "]"
