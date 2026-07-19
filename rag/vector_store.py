"""Embedding-backed document vector store built on Chroma.

This module owns the retrieval index. Document chunks produced by
``rag.ingest`` are embedded with a sentence-transformer model
(``all-MiniLM-L6-v2`` via Chroma's default ONNX embedding function) and stored
in a Chroma collection. Retrieval is a semantic nearest-neighbour search over
those embeddings, not lexical token overlap.

For the project's own documents (``config.DOCS_PATH``) the index is persisted on
disk at ``config.VECTOR_STORE_PATH`` so it survives between runs. For any other
docs path (tests, ad-hoc corpora) an in-memory index is built on demand. Both
paths are cached per resolved docs path so repeated queries do not re-embed.
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions

from config import DOCS_PATH, VECTOR_STORE_PATH
from rag.ingest import ingest_documents

COLLECTION_NAME = "sales_documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Cosine similarity below this is treated as "no relevant match". Calibrated on
# the shipped corpus: genuine business queries score >= 0.26, whereas nonsense
# queries score <= 0.15, so 0.2 separates them with margin. See
# docs/modeling/retrieval_threshold.md.
MIN_SIMILARITY = 0.2

_collection_cache: dict[str, Collection | None] = {}


def _embedding_function() -> embedding_functions.EmbeddingFunction:
    return embedding_functions.DefaultEmbeddingFunction()


def _build_collection(client: chromadb.ClientAPI, docs_path: Path) -> Collection | None:
    chunks = ingest_documents(docs_path=docs_path)
    if not chunks:
        return None

    # Recreate cleanly so a rebuild never leaves stale chunks behind.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=[chunk.chunk_id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        metadatas=[{"source": chunk.source, "chunk_id": chunk.chunk_id} for chunk in chunks],
    )
    return collection


def get_collection(
    docs_path: Path = DOCS_PATH,
    persist_dir: Path = VECTOR_STORE_PATH,
    rebuild: bool = False,
) -> Collection | None:
    """Return the Chroma collection for ``docs_path``, building it if needed.

    The default corpus is persisted to ``persist_dir``; other corpora use an
    in-memory client. Returns ``None`` when the docs path yields no chunks.
    """
    cache_key = str(Path(docs_path).resolve())
    if not rebuild and cache_key in _collection_cache:
        return _collection_cache[cache_key]

    is_default_corpus = cache_key == str(Path(DOCS_PATH).resolve())
    if is_default_corpus:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(persist_dir))
    else:
        client = chromadb.EphemeralClient()

    collection = _build_collection(client, Path(docs_path))
    _collection_cache[cache_key] = collection
    return collection


def clear_cache() -> None:
    """Drop the in-process collection cache (used by tests)."""
    _collection_cache.clear()
